from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
from logging import getLogger
from sandal.command import CommandError
from .context import get_current_http_response

LOGGER = getLogger(__name__)

def raise_http_error(status_code, body=None):
    raise HTTPError(status_code, body)


def end_http_request_processing():
    raise HTTPError(None)


class HTTPError(Exception):
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self.body = body


@contextlib.contextmanager
def handle_exception():
    response = get_current_http_response()
    try:
        yield
    except HTTPError, e:
        if e.status_code:
            response.status_code = e.status_code
        if e.body is not None:
            response.write(e.body)
        response.finish()
    except CommandError, e:
        response.status_code = httplib.INTERNAL_SERVER_ERROR
        response.write(e.message)
        response.finish()
    except:
        LOGGER.exception('failed to handle http request')
        try:
            response.status_code = httplib.INTERNAL_SERVER_ERROR
            response.finish()
        except:
            LOGGER.exception('failed to finish the request')
