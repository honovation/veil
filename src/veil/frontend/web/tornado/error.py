from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
from logging import getLogger
from veil.model.security import *
from .context import get_current_http_request
from .context import get_current_http_response

LOGGER = getLogger(__name__)


def end_http_request_processing():
    raise HTTPError(None)


class HTTPError(Exception):
    EXPECTED_WIDGET_ERROR = 'true'

    def __init__(self, status_code, message=None):
        super(HTTPError, self).__init__()
        self.status_code = status_code
        self.message = message


@contextlib.contextmanager
def handle_exception():
    request = get_current_http_request()
    response = get_current_http_response()
    try:
        yield
    except HTTPError as e:
        if e.status_code:
            response.status_code = e.status_code
        if e.message is not None:
            response.write(e.message)
        response.finish()
    except PermissionDenied as e:
        response.status_code = httplib.FORBIDDEN
        response.write(e.message)
        response.finish()
    except Exception:
        LOGGER.exception('failed to handle http request: %(site)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
            'site': request.host,
            'uri': request.uri,
            'referer': request.headers.get('Referer'),
            'remote_ip': request.remote_ip,
            'user_agent': request.headers.get('User-Agent')
        })
        response.status_code = httplib.INTERNAL_SERVER_ERROR
        try:
            response.finish()
        except Exception:
            LOGGER.exception('failed to finish the request')
