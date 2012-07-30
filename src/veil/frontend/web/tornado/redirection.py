from __future__ import unicode_literals, print_function, division
import httplib
import urlparse
import re
from .context import get_current_http_response
from .error import end_http_request_processing
from veil.model.encoding import to_str

def redirect_to(url, permanent=False, response=None):
    response = response or get_current_http_response()
    if response.headers_written:
        raise Exception('Cannot redirect after headers have been written')
    response.status_code = httplib.MOVED_PERMANENTLY if permanent else httplib.FOUND
    # Remove whitespace
    url = re.sub(r'[\x00-\x20]+', '', to_str(url))
    response.set_header('Location', urlparse.urljoin(response.request.uri, url))
    end_http_request_processing()
