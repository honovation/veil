from __future__ import unicode_literals, print_function, division
import os.path
import re
import contextlib
import httplib
from inspect import isfunction
from logging import getLogger
from urllib import unquote
from sandal.component import force_import_module
from sandal.template import *
from veil.http import *

LOGGER = getLogger(__name__)
routes = {}


def route(method, path_template, website=None, tags=(), **path_template_params):
    def create_and_register_route(route_handler):
        _website = website
        if not _website:
            _website = infer_website_from_module_name(route_handler.__module__)
        if not _website:
            raise Exception('website not specified for route: {}'.format(route_handler))
        new_route = Route(page(route_handler), method, path_template, tags=tags, **path_template_params)
        routes.setdefault(_website, []).append(new_route)
        return route_handler

    return create_and_register_route


def infer_website_from_module_name(qualified_module_name):
    module_name = qualified_module_name.split('.')[-1]
    if module_name.startswith('_'):
        module_name = module_name[1:]
    if module_name.endswith('_web'):
        return module_name.replace('_web', '').upper()
    return None


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
    return routes.get(website, ())


class RoutingHTTPHandler(object):
    def __init__(self, routes, context_managers):
        self.routes = routes
        self.context_managers = context_managers

    def __call__(self):
        for route in self.routes:
            if self.try_route(route):
                return
        raise_http_error(httplib.NOT_FOUND)

    def try_route(self, route):
        with require_current_template_directory_being(get_route_handler_template_directory(route.route_handler)):
            request = get_current_http_request()
            if route.method.upper() != request.method.upper():
                return False
            path_arguments = route.path_template.match(request.path)
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
                response.write(data)
            if 'ASYNC' not in route.tags:
                response.finish()
        except:
            LOGGER.error('failed to post-process route: {}'.format(route))
            raise


def get_route_handler_template_directory(route_handler):
    return os.path.dirname(force_import_module(route_handler.__module__).__file__)


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
    PATH_TEMPLATE_PARAMETER_REGEX = re.compile(r'\{\{(.*?)\}\}')

    def __init__(self, template, template_params):
        self.validate(template, template_params)
        self.template = template
        self.template_params = template_params

    @classmethod
    def validate(cls, template, template_params):
        matches = cls.PATH_TEMPLATE_PARAMETER_REGEX.findall(template)
        present_params = list(match.strip() for match in matches)
        if set(present_params) != set(template_params.keys()):
            raise Exception('{} present, actually provided {}'.format(present_params, template_params))

    def translate_to_regex(self):
        def replace_placeholder(match):
            param_name = match.group(1).strip()
            param_regex = self.template_params[param_name]
            return '(?P<{}>{})'.format(param_name, param_regex)

        path_regex = self.template.replace('.', '\.') + '$'
        path_regex = self.PATH_TEMPLATE_PARAMETER_REGEX.sub(replace_placeholder, path_regex)
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
