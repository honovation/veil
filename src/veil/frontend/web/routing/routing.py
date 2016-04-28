from __future__ import unicode_literals, print_function, division

import contextlib
import functools
import httplib
import re
from inspect import isfunction
from logging import getLogger
from urllib import unquote
from urlparse import urlparse
from user_agents import parse

from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web.tornado import *
from veil.model.command import *
from veil.model.collection import *
from veil.model.event import *
from veil.utility.encoding import *
from veil.utility.json import *
from veil.utility.memoize import *
import veil_component

from ..website_installer import EVENT_NEW_WEBSITE, get_website_parent_domain

from .page_post_processor import post_process_page

LOGGER = getLogger(__name__)
TAG_NO_LOGIN_REQUIRED = 'PUBLIC'
original_routes = {}
routes = {}


@test_hook
def remember_original_routes():
    get_executing_test().addCleanup(reset_routes)
    global original_routes
    if not original_routes:
        original_routes = dict(routes)


def reset_routes():
    routes.clear()
    if original_routes:
        routes.update(original_routes)


class RouteDecorator(object):
    def __init__(self, method, path_template, website, tags=(), delegates_to=None, **path_template_params):
        assert website
        self.method = method
        self.path_template = path_template
        self.website = website.lower()
        self.tags = tags
        self.delegates_to = delegates_to
        self.path_template_params = path_template_params
        veil_component.record_dynamic_dependency_provider(veil_component.get_loading_component_name(), 'website', self.website)
        publish_new_website_event(self.website)

    def __call__(self, func):
        target = self.delegates_to or func
        widget_namespace = veil_component.get_loading_component_name() or None

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with require_current_template_directory_relative_to(target):
                with require_current_widget_namespace_being(widget_namespace):
                    return func(*args, **kwargs)
        if self.delegates_to:
            wrapper.__name__ = b'{}-{}'.format(func.__name__, self.delegates_to.__name__)

        new_route = Route(route_handler=wrapper, method=self.method, path_template=self.path_template, tags=self.tags, **self.path_template_params)
        routes.setdefault(self.website, []).append(new_route)
        return wrapper


def publish_new_website_event(website):
    publish_event(EVENT_NEW_WEBSITE, website=website.lower())


def route(method, path_template, website, tags=(), delegates_to=None, **path_template_params):
    return RouteDecorator(method=method, path_template=path_template, website=website, tags=tags, delegates_to=delegates_to, **path_template_params)


def route_for(website, tags=()):
    return functools.partial(route, website=website, tags=tags)


def async_route(*args, **kwargs):
    kwargs['tags'] = set(kwargs.get('tags', ())) | {'ASYNC'}
    return route(*args, **kwargs)


def public_route(*args, **kwargs):
    kwargs['tags'] = set(kwargs.get('tags', ())) | {TAG_NO_LOGIN_REQUIRED}
    return route(*args, **kwargs)


def is_public_route(route):
    return TAG_NO_LOGIN_REQUIRED in route.tags


def get_routes(website):
    website = website.lower()
    return routes.get(website, ())


class RoutingHTTPHandler(object):
    def __init__(self, website, context_managers):
        self.website = website
        self.routes = get_routes(website)
        self.context_managers = context_managers

    def __call__(self):
        request = get_current_http_request()
        request.website = self.website
        request.user_agent = parse_user_agent(request.headers.get('User-Agent'))
        request.is_ajax = request.headers.get('X-Requested-With') == b'XMLHttpRequest'
        request.website_url = '{}://{}'.format(request.protocol, request.host)
        record_request_referrer(request)
        for route in self.routes:
            if self.try_route(request, route):
                return
        raise HTTPError(httplib.NOT_FOUND)

    def try_route(self, request, route):
        if not is_method_matched(route.method, request.method):
            return False
        path = request.path or '/'
        path_arguments = route.path_template.match(path)
        if path_arguments is None:
            return False
        assert getattr(request, 'route', None) is None
        try:
            request.route = route
            if self.context_managers:
                with nest_context_managers(*self.context_managers):
                    self.execute_route(route, path_arguments)
            else:
                self.execute_route(route, path_arguments)
        finally:
            request.route = None
        return True

    @staticmethod
    def execute_route(route, path_arguments):
        request = get_current_http_request()
        response = get_current_http_response()
        for name, value in path_arguments.items():
            request.arguments.setdefault(name, []).extend((value,))
        try:
            data = route.route_handler()
        except InvalidCommand as e:
            set_http_status_code(httplib.BAD_REQUEST)
            data = e.errors
        not_head_request = request.method != 'HEAD'
        responsed_in_json = 'application/json' in response.headers.get('Content-Type', '')
        if responsed_in_json or data is not None and not isinstance(data, basestring) or 'application/json' in request.headers.get('Accept', ''):
            if not responsed_in_json:
                response.set_header('Content-Type', 'application/json; charset=UTF-8')
            if not_head_request:
                data = to_readable_json(data)
        else:
            if not_head_request and data is not None:
                try:
                    data = post_process_page(route.route_handler, data)
                except Exception:
                    LOGGER.error('failed to post-process route: %(route)s', {'route': route})
                    raise
        if not_head_request and data is not None:
            response.write(data)
        if 'ASYNC' not in route.tags:
            response.finish()


def is_method_matched(route_method, request_method):
    return route_method == request_method or ('GET' == route_method and 'HEAD' == request_method)


def nest_context_managers(*context_managers):
    context_managers = [as_context_manager(obj) for obj in context_managers]
    return contextlib.nested(*context_managers)


def as_context_manager(obj):
    if isfunction(obj):
        return obj()
    if hasattr(obj, '__enter__') and hasattr(obj, '__exit__'):
        return obj
    raise Exception('{} is not context manager'.format(obj))


class Route(object):
    def __init__(self, route_handler, method, path_template, tags=(), **path_template_params):
        self.route_handler = route_handler
        self.method = method
        self.path_template = PathTemplate(path_template, path_template_params)
        self.tags = tags if isinstance(tags, set) else set(tags)

    def __repr__(self):
        return '{} {}'.format(self.method, self.path_template)


class PathTemplate(object):
    REGEX_PATH_TEMPLATE_PARAMETER = re.compile(r'\{\{(.*?)\}\}')

    def __init__(self, template, template_params):
        self.validate(template, template_params)
        self.template = template
        self.template_params = template_params

    @classmethod
    def validate(cls, template, template_params):
        matches = cls.REGEX_PATH_TEMPLATE_PARAMETER.findall(template)
        present_params = list(match.strip() for match in matches)
        if set(present_params) != set(template_params):
            raise Exception('{} present, actually provided {}'.format(present_params, template_params))

    def translate_to_regex(self):
        def replace_placeholder(match):
            param_name = match.group(1).strip()
            param_regex = self.template_params[param_name]
            return '(?P<{}>{})'.format(param_name, param_regex)

        path_regex = self.template.replace('.', '\.') + '$'
        path_regex = self.REGEX_PATH_TEMPLATE_PARAMETER.sub(replace_placeholder, path_regex)
        return path_regex

    def get_compiled_regex(self):
        if not hasattr(self, '_regex'):
            setattr(self, '_regex', re.compile(self.translate_to_regex()))
        return getattr(self, '_regex')

    def match(self, path):
        regex = self.get_compiled_regex()
        match = regex.match(path)
        if match is None:
            return None
        kwargs = {k: unquote(v) for k, v in match.groupdict().items() if v}  # ignore empty arguments and keep consistent with normalize_arguments
        return kwargs

    def __repr__(self):
        return '{} {}'.format(self.template, self.template_params)


@memoize(maxsize=2 ** 15, timeout=60 * 20)
def parse_user_agent(user_agent):
    ua = parse(user_agent or '')
    ua.is_from_weixin = b'MicroMessenger' in ua.ua_string
    return ua


def record_request_referrer(request):
    request.referrer = DictObject(raw=request.headers.get('Referer'), text='', host='', from_internal=False)
    if request.referrer.raw:
        request.referrer.text = to_unicode(request.referrer.raw, strict=False, additional={
            'uri': request.uri,
            'referer': request.referrer.raw,
            'remote_ip': request.remote_ip,
            'user_agent': request.user_agent.ua_string
        })
        request.referrer.host = urlparse(request.referrer.text).hostname
        if request.referrer.host:
            request.referrer.host = request.referrer.host.strip('.')
            request.referrer.from_internal = request.referrer.host.endswith(get_website_parent_domain(request.website))


@template_utility
def is_requested_from_spider():
    request = get_current_http_request()
    return request and request.user_agent.is_bot
