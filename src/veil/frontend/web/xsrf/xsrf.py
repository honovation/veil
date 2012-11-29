from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
import uuid
from logging import getLogger
from markupsafe import Markup
from tornado.escape import xhtml_escape
from veil.frontend.template import template_utility
from veil.frontend.web.tornado import *

LOGGER = getLogger(__name__)

@contextlib.contextmanager
def prevent_xsrf():
    request = get_current_http_request()
    response = get_current_http_response()
    if not hasattr(request, '_xsrf_token'):
        token = get_cookie(name='_xsrf', request=request)
        request.is_new_xsrf_token = False
        if not token:
            request.is_new_xsrf_token = True
            token = uuid.uuid4().get_hex()
            LOGGER.debug('assigned XSRF token: %(token)s from %(method)s %(path)s', {
                'token': token,
                'method': request.method,
                'path': request.path
            })
        request._xsrf_token = token
    if 'GET' != request.method.upper():
        token = get_http_argument('_xsrf', optional=True) or request.headers.get('X-XSRF', None)
        if not token:
            response.status_code = httplib.FORBIDDEN
            LOGGER.warn('XSRF token not found: request is %(request)s', {'request': str(request)})
            raise HTTPError(403, 'XSRF token missing')
        expected_token = xsrf_token()
        if expected_token != token:
            LOGGER.warn('XSRF token invalid: request is %(request)s, expected is %(expected_token)s, actual is %(token)s', {
                'request': request,
                'expected_token': expected_token,
                'token': token
            })
            raise HTTPError(403, 'XSRF token invalid')
    request.arguments.pop('_xsrf', None)
    yield


def set_xsrf_cookie_for_page(route_handler, data):
    if get_current_http_request().is_new_xsrf_token:
        if data and '<html' in data.lower():
            # only set to page to avoid concurrent http request issue
            set_cookie(name='_xsrf', value=xsrf_token())
    return data


@template_utility
def xsrf_token(request=None):
    request = request or get_current_http_request()
    assert request._xsrf_token is not None
    return request._xsrf_token


@template_utility
def xsrf_field():
    return Markup('<input type="hidden" name="_xsrf" value="{}"/>'.format(xhtml_escape(xsrf_token())))