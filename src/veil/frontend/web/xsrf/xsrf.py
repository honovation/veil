from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
import uuid
from logging import getLogger
from markupsafe import Markup
from veil.frontend.template import template_utility
from veil.frontend.web.tornado import *
from tornado.escape import xhtml_escape
from veil.frontend.web.static_file import static_url

LOGGER = getLogger(__name__)

@contextlib.contextmanager
def prevent_xsrf():
    request = get_current_http_request()
    response = get_current_http_response()
    if not hasattr(request, '_xsrf_token'):
        token = get_cookie(name='_xsrf', request=request)
        if not token:
            token = uuid.uuid4().get_hex()
            LOGGER.debug('assign XSRF token {} from {} {}'.format(token, request.method, request.path))
        request._xsrf_token = token
    if 'GET' != request.method.upper():
        token = get_http_argument('_xsrf', optional=True) or request.headers.get('X-XSRF', None)
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


def xsrf_script_elements_processor(parser, script_elements):
    script = parser.makeelement(
        'script', attrib={'type': 'text/javascript'})
    script.text =\
    """
    $.cookie('_xsrf', '%s', {path: '/'});
    $.ajaxSetup({headers:{'X-XSRF':$.cookie('_xsrf')}});
    """ % xsrf_token()
    new_script_elements = [
        parser.makeelement(
            'script', attrib={
                'type': 'text/javascript',
                'src': static_url('jquery.js')
            }),
        parser.makeelement(
            'script', attrib={
                'type': 'text/javascript',
                'src': static_url('jquery-cookie.js')
            }),
        parser.makeelement(
            'script', attrib={
                'type': 'text/javascript',
                'src': static_url('veil.js')
            }),
        script]
    new_script_elements.extend(script_elements)
    return new_script_elements


@template_utility
def xsrf_token(request=None):
    request = request or get_current_http_request()
    assert request._xsrf_token is not None
    return request._xsrf_token


@template_utility
def xsrf_field():
    return Markup('<input type="hidden" name="_xsrf" value="{}"/>'.format(xhtml_escape(xsrf_token())))