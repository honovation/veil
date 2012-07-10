from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
import uuid
from logging import getLogger
from markupsafe import Markup
from sandal.encoding import encode_xhtml
from sandal.template import template_utility
from .argument import try_get_http_argument
from .cookie import get_cookie, set_cookie
from .error import HTTPError
from .context import get_current_http_request
from .context import get_current_http_response

LOGGER = getLogger(__name__)

@contextlib.contextmanager
def prevent_xsrf():
    request = get_current_http_request()
    response = get_current_http_response()
    if not hasattr(request, '_xsrf_token'):
        token = get_cookie(name='_xsrf', request=request)
        if not token:
            token = uuid.uuid4().get_hex()
            set_cookie(name='_xsrf', value=token, response=response)
        request._xsrf_token = token
    if 'GET' != request.method.upper():
        token = try_get_http_argument('_xsrf') or request.headers.get('X-XSRF', None)
        if not token:
            response.status_code = httplib.FORBIDDEN
            LOGGER.warn('XSRF token missing, request: {}'.format(request))
            raise HTTPError(403, 'XSRF token missing')
        expected_token = xsrf_token()
        if expected_token != token:
            LOGGER.debug('expected token: {}'.format(expected_token))
            LOGGER.debug('actual token: {}'.format(token))
            LOGGER.warn('XSRF token invalid, request: {}'.format(request))
            raise HTTPError(403, 'XSRF token invalid')
    request.arguments.pop('_xsrf', None)
    yield


@template_utility
def xsrf_token(request=None):
    request = request or get_current_http_request()
    assert request._xsrf_token is not None
    return request._xsrf_token


@template_utility
def xsrf_field():
    return Markup('<input type="hidden" name="_xsrf" value="{}"/>'.format(encode_xhtml(xsrf_token())))
