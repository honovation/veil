from __future__ import unicode_literals, print_function, division
import functools
import re
import contextlib
import httplib
from inspect import isfunction
from logging import getLogger
from urllib import unquote
from veil.utility.json import *
from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web.tornado import *
from veil.model.event import *
from veil.model.command import *
import veil_component
from .page_post_processor import post_process_page

LOGGER = getLogger(__name__)
original_routes = {}
routes = {}
EVENT_NEW_WEBSITE = define_event('new-website')

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
        assert website is not None
        self.method = method
        self.path_template = path_template
        self.website = website.lower()
        self.tags = tags
        self.delegates_to = delegates_to
        self.path_template_params = path_template_params
        publish_new_website_event(self.website)

    def __call__(self, func):
        target = self.delegates_to or func
        loading_component_name = veil_component.get_loading_component_name()
        if loading_component_name:
            veil_component.record_dynamic_dependency_provider(loading_component_name, 'website', self.website)
            widget_namespace = loading_component_name
        else:
            widget_namespace = None

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with require_current_template_directory_relative_to(target):
                with require_current_widget_namespace_being(widget_namespace):
                    return func(*args, **kwargs)

        new_route = Route(
            route_handler=wrapper, method=self.method, path_template=self.path_template,
            tags=self.tags, **self.path_template_params)
        routes.setdefault(self.website, []).append(new_route)
        return wrapper


def publish_new_website_event(website):
    publish_event(EVENT_NEW_WEBSITE, website=website.lower())


def route(method, path_template, website, tags=(), delegates_to=None, **path_template_params):
    return RouteDecorator(
        method=method, path_template=path_template,
        website=website, tags=tags, delegates_to=delegates_to,
        **path_template_params)


def route_for(website, tags=()):
    return functools.partial(route, website=website, tags=tags)


def async_route(*args, **kwargs):
    kwargs['tags'] = set(kwargs.get('tags', ()))
    kwargs['tags'].add('ASYNC')
    return route(*args, **kwargs)


def public_route(*args, **kwargs):
    kwargs['tags'] = set(kwargs.get('tags', ()))
    kwargs['tags'].add('PUBLIC')
    return route(*args, **kwargs)


def is_public_route(route):
    return 'PUBLIC' in route.tags


def get_routes(website):
    website = website.lower()
    return routes.get(website, ())


class RoutingHTTPHandler(object):
    def __init__(self, routes, context_managers):
        self.routes = routes
        self.context_managers = context_managers

    def __call__(self):
        for route in self.routes:
            if self.try_route(route):
                return
        raise HTTPError(httplib.NOT_FOUND)

    def try_route(self, route):
        request = get_current_http_request()
        if not is_method_matched(route.method.upper(), request.method.upper()):
            return False
        path = request.path.rstrip(b'/')
        if not path:
            path = '/'
        path_arguments = route.path_template.match(path)
        if path_arguments is None:
            return False
        assert getattr(get_current_http_context(), 'route', None) is None
        try:
            get_current_http_context().route = route
            if self.context_managers:
                with nest_context_managers(*self.context_managers):
                    self.execute_route(route, path_arguments)
            else:
                self.execute_route(route, path_arguments)
        finally:
            get_current_http_context().route = None
        return True

    def execute_route(self, route, path_arguments):
        request = get_current_http_request()
        response = get_current_http_response()
        for name, value in path_arguments.items():
            request.arguments.setdefault(name, []).extend((value,))
        try:
            data = route.route_handler()
        except InvalidCommand as e:
            set_http_status_code(httplib.BAD_REQUEST)
            data = e.errors
        not_head_request = request.method.upper() != 'HEAD'
        if 'application/json' in request.headers.get('Accept', '') or isinstance(data, dict):
            response.set_header('Content-Type', 'application/json; charset=UTF-8')
            if not_head_request:
                data = to_json(data)
        else:
            if not_head_request and data is not None:
                try:
                    data = post_process_page(route.route_handler, data)
                except:
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
        self.tags = set(tags)

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
        if set(present_params) != set(template_params.keys()):
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
        kwargs = dict((k, None if v is None else unquote(v)) for (k, v) in match.groupdict().iteritems())
        return kwargs

    def __repr__(self):
        return '{} {}'.format(self.template, self.template_params)
