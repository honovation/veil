"""
Request arguments:

parse arguments from request query, request body and request path
merge values if the argument exists in request query, request body and request path

strip whitespaces from request query values
strip whitespaces from non-json request body values
in terms of json request body values, keep whitespaces if requested from api, otherwise whitespaces are removed by $.serializeObject in veil.js

remove arguments with blank values
"""
from __future__ import unicode_literals, print_function, division
import logging
import contextlib
import re
import traceback
from veil.model.collection import *
from veil.model.command import *
from veil.utility.encoding import *
from veil.utility.json import *
from .context import get_current_http_request

LOGGER = logging.getLogger(__name__)

SHOULD_BE_DELETED_ARGUMENT_PREFIX = b'_v_'


@contextlib.contextmanager
def normalize_arguments():
    request = get_current_http_request()
    arguments = request.arguments
    for field in arguments.keys():
        if field.startswith(SHOULD_BE_DELETED_ARGUMENT_PREFIX):
            del arguments[field]
            continue
        value = []
        for v in arguments[field]:
            v = to_unicode(v, strict=False, additional={
                    'field': field,
                    'uri': request.uri,
                    'referer': request.headers.get('Referer'),
                    'remote_ip': request.remote_ip,
                    'user_agent': request.headers.get('User-Agent')
                })
            v = re.sub(r'[\x00-\x08\x0e-\x1f]', ' ', v)
            v = v.strip()
            if v:
                value.append(v)
        if value:
            arguments[field] = value
        else:
            del arguments[field]
    if request.headers.get('X-Upload-File-Path'):
        arguments['upload-file-path'] = [to_unicode(request.headers.get('X-Upload-File-Path'), strict=False)]

    # parse request body in ``application/json`` as tornado's parse_body_arguments does not support it
    if request.headers.get('Content-Type', '').startswith('application/json'):
        json_arguments = objectify(from_json(request.body or '{}'))
        value_contained_in_array = json_arguments.pop('value_contained_in_array', False)
        for name, value in json_arguments.items():
            request.arguments.setdefault(name, []).extend(value if value_contained_in_array else [value])
    yield


def delete_http_argument(field, request=None):
    request = request or get_current_http_request()
    request.arguments.pop(field, None)


def get_http_argument(field, default=None, request=None, list_field=False, optional=False, to_type=None):
    request = request or get_current_http_request()
    if field not in request.arguments:
        if optional:
            if list_field:
                return default or []
            else:
                return default
        if default is not None:
            return default
        LOGGER.error('http argument not found: field %(field)s can not be found among %(arguments)s\n%(stack_trace)s', {
            'field': field,
            'arguments': request.arguments,
            'stack_trace': b''.join(traceback.format_stack())
        })
        raise InvalidCommand({field: 'not provided'})
    values = request.arguments[field]
    if to_type:
        if list_field:
            return [None if v is None else to_type(v) for v in values]
        else:
            return None if values[0] is None else to_type(values[0])
    else:
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


def get_http_arguments(request=None, **kwargs):
    request = request or get_current_http_request()
    arguments = DictObject()
    for field, values in request.arguments.items():
        arguments[field] = get_http_argument(field, request=request, list_field=len(values) > 1)
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
def tunnel_put_and_patch_and_delete():
    request = get_current_http_request()
    tunnelled_method = request.arguments.pop('_method', None)
    if 'POST' == request.method and tunnelled_method:
        request.method = tunnelled_method
    yield
