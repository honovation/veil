from __future__ import unicode_literals, print_function, division
import functools
import re
import contextlib
import httplib
from inspect import isfunction
from logging import getLogger
from urllib import unquote
from veil.development.test import *
from veil.component import *
from veil.frontend.template import *
from veil.frontend.web.tornado import *
from veil.model.event import *
from .page_post_processor import post_process_page

LOGGER = getLogger(__name__)
original_routes = {}
routes = {}
website_components = {}
EVENT_NEW_WEBSITE = 'new-website'


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
    def __init__(self, method, path_template, website=None, tags=(), delegates_to=None, **path_template_params):
        self.method = method
        self.path_template = path_template
        self.website = (website or infer_website()).upper()
        self.tags = tags
        self.delegates_to = delegates_to
        self.path_template_params = path_template_params
        publish_new_website_event(self.website)

    def __call__(self, func):
        target = self.delegates_to or func
        loading_component = get_loading_component()
        if loading_component:
            widget_namespace = loading_component.__name__
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
    if website in website_components:
        if get_loading_component():
            website_components[website].add(get_loading_component())
    else:
        website_components.setdefault(website, set()).add(get_loading_component())
        publish_event(EVENT_NEW_WEBSITE, website=website)


def route(method, path_template, website=None, tags=(), delegates_to=None, **path_template_params):
    return RouteDecorator(
        method=method, path_template=path_template,
        website=website, tags=tags, delegates_to=delegates_to,
        **path_template_params)


def route_for(website):
    return functools.partial(route, website=website)


def infer_website():
    return get_loading_component().__name__.split('.')[-1].upper()


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
    website = website.upper()
    components = website_components.get(website, ())
    for component in components:
        if component:
            assert_component_loaded(component.__name__)
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
        if route.method.upper() != request.method.upper():
            return False
        path = request.path.rstrip('/')
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
        request.arguments.update(dict([(k, (v,)) for k, v in path_arguments.items()]))
        data = route.route_handler()
        try:
            if data is not None:
                data = post_process_page(route.route_handler, data)
                response.write(data)
            if 'ASYNC' not in route.tags:
                response.finish()
        except:
            LOGGER.error('failed to post-process route: {}'.format(route))
            raise


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
