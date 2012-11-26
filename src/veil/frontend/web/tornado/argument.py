from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
import logging
import re
import traceback
from veil.model.collection import *
from veil.utility.encoding import *
from .error import  HTTPError
from .context import get_current_http_request

LOGGER = logging.getLogger(__name__)

@contextlib.contextmanager
def normalize_arguments():
    arguments = get_current_http_request().arguments
    for field in arguments:
        values = arguments[field]
        values = [re.sub(r'[\x00-\x08\x0e-\x1f]', ' ', x) for x in values]
        values = [to_unicode(x) for x in values]
        values = [x.strip() for x in values]
        arguments[field] = values
    yield


def delete_http_argument(field, request=None):
    request = request or get_current_http_request()
    request.arguments.pop(field, None)


def get_http_argument(field, default=None, request=None, list_field=False, optional=False):
    request = request or get_current_http_request()
    if field not in request.arguments:
        if optional:
            if list_field:
                return []
            else:
                return None
        if default is not None:
            return default
        LOGGER.error('http argument not found: field %(field)s can not be found among %(arguments)s\n%(stack_trace)s', {
            'field': field,
            'arguments': request.arguments,
            'stack_trace': str('').join(traceback.format_stack())
        })
        raise HTTPError(httplib.BAD_REQUEST, '{} not found in http arguments: {}'.format(field, request.arguments))
    values = request.arguments[field]
    return values if list_field else values[0]


def get_http_file(field, default=None, request=None, list_field=False, optional=False):
    request = request or get_current_http_request()
    if field not in request.files:
        if optional:
            return None
        if default is not None:
            return default
        raise Exception('{} not found in http files: {}'.format(field, request.files))
    values = request.files[field]
    return [DictObject(value) for value in values] if list_field else DictObject(values[0])


def get_http_arguments(request=None, list_fields=(), **kwargs):
    request = request or get_current_http_request()
    arguments = DictObject()
    for field, values in request.arguments.items():
        arguments[field] = get_http_argument(field, request=request, list_field=field in list_fields)
    arguments.update(kwargs)
    return arguments


def clear_http_arguments(request=None):
    request = request or get_current_http_request()
    request.arguments.clear()


def get_http_files(request=None, list_fields=(), **kwargs):
    request = request or get_current_http_request()
    files = DictObject()
    for field, values in request.files.items():
        files[field] = get_http_file(field, request=request, list_field=field in list_fields)
    files.update(kwargs)
    return files


@contextlib.contextmanager
def tunnel_put_and_delete():
    request = get_current_http_request()
    tunnelled_method = get_http_argument('_method', optional=True)
    if 'POST' == request.method.upper() and tunnelled_method:
        request.method = tunnelled_method
    request.arguments.pop('_method', None)
    yield
