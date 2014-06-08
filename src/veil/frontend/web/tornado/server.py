from __future__ import print_function, division
import calendar
import datetime
import email.utils
import functools
import hashlib
import httplib
from logging import getLogger
import re
import tornado
import traceback
import Cookie
from tornado.httpserver import HTTPServer
from tornado.stack_context import StackContext
from tornado.ioloop import IOLoop
from veil.utility.encoding import to_str
from veil.development.test import *
from .argument import normalize_arguments
from .argument import tunnel_put_and_delete
from .context import HTTPContext
from .context import require_current_http_context_being
from .context import get_current_http_response
from .error import handle_exception

LOGGER = getLogger(__name__)

def start_http_server(handler, io_loop=None, host='127.0.0.1', port=8080, process_count=1):
    io_loop = io_loop or IOLoop.instance()
    http_server = create_http_server(handler, io_loop=io_loop)
    http_server.bind(port, host)
    http_server.start(process_count)
    io_loop.add_callback(lambda: LOGGER.info('ioloop started: listening at %(host)s:%(port)s', {'host': host, 'port': port}))
    io_loop.start()


def start_test_http_server(handler, host='127.0.0.1', port=8080):
    http_server = create_http_server(handler)
    http_server.host = host
    http_server.port = port
    http_server.listen(port, host)
    get_executing_test().addCleanup(http_server.stop)
    return http_server


def create_http_server(handler, **kwargs):
    return HTTPServer(HTTPHandler(handler), xheaders=True, **kwargs)


class HTTPHandler(object):
    def __init__(self, handler):
        self.handler = handler

    def __call__(self, request):
        http_context = HTTPContext(request, HTTPResponse(request))
        with create_stack_context(require_current_http_context_being, http_context=http_context):
            with create_stack_context(handle_exception):
                with normalize_arguments():
                    with tunnel_put_and_delete():
                        self.handler()
        LOGGER.debug('handled request: %(request)s', {'request': unicode(request)})


def create_stack_context(context_manager, *args, **kwargs):
    return StackContext(functools.partial(context_manager, *args, **kwargs))


def set_http_status_code(status_code):
    get_current_http_response().status_code = status_code


class HTTPResponse(object):
    def __init__(self, request):
        self._headers_written = None
        self._finished = False
        self._cookies = Cookie.SimpleCookie()
        self.request = request
        self.connection = self.request.connection
        self.clear()

    @property
    def finished(self):
        return self._finished

    @property
    def headers(self):
        return self._headers

    @property
    def headers_written(self):
        return self._headers_written

    @property
    def cookies(self):
        return self._cookies

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, status_code):
        assert status_code in httplib.responses
        if self.headers_written:
            LOGGER.warn('setting status code too late: status code to set is %(status_code)s\n%(headers_written)s', {
                'status_code': status_code,
                'headers_written': self.headers_written
            })
        self._status_code = status_code

    def clear(self):
        self._headers = {
            'Server': 'TornadoServer/{}'.format(tornado.version),
            'Content-Type': 'text/html; charset=UTF-8',
        }
        if not self.request.supports_http_1_1():
            if self.request.headers.get('Connection') == 'Keep-Alive':
                self.set_header('Connection', 'Keep-Alive')
        self._write_buffer = []
        self._status_code = 200

    def set_header(self, name, value):
        if self.headers_written:
            LOGGER.warn('setting header too late: header to set is %(name)s=%(value)s\n%(headers_written)s', {
                'name': name,
                'value': value,
                'headers_written': self.headers_written
            })
        if isinstance(value, datetime.datetime):
            t = calendar.timegm(value.utctimetuple())
            value = email.utils.formatdate(t, localtime=False, usegmt=True)
        elif isinstance(value, int) or isinstance(value, long):
            value = str(value)
        else:
            value = to_str(value)
            # If \n is allowed into the header, it is possible to inject
            # additional headers or split the request. Also cap length to
            # prevent obviously erroneous values.
            safe_value = re.sub(r'[\x00-\x1f]', ' ', value)[:4000]
            if safe_value != value:
                raise ValueError('Unsafe header value %r', value)
        self._headers[to_str(name)] = value

    def clear_header(self, name):
        """Clears an outgoing header, undoing a previous `set_header` call.

        Note that this method does not apply to multi-valued headers
        set by `add_header`.
        """
        name = to_str(name)
        if name in self._headers:
            del self._headers[name]

    def _clear_headers_for_304(self):
        # 304 responses should not contain entity headers (defined in
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec7.html#sec7.1)
        # not explicitly allowed by
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.5
        headers = ['Allow', 'Content-Encoding', 'Content-Language', 'Content-Length', 'Content-MD5', 'Content-Range', 'Content-Type', 'Last-Modified']
        for h in headers:
            self.clear_header(h)

    def write(self, chunk):
        assert not self._finished
        chunk = to_str(chunk)
        self._write_buffer.append(chunk)

    def flush(self):
        if not self._headers_written:
            self._headers_written = traceback.format_stack()
            headers = self._generate_headers()
        else:
            headers = ''

        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == 'HEAD':
            if headers:
                self.connection.write(headers)
            return

        chunk = ''.join(self._write_buffer)
        self._write_buffer = []
        if headers or chunk:
            self.connection.write(headers + chunk)

    def finish(self, no_keep_alive=False):
        assert not self._finished

        # Automatically support ETags and add the Content-Length header if
        # we have not flushed any content yet.
        if not self._headers_written:
            if (self._status_code == 200 and self.request.method in ('GET', 'HEAD') and 'Etag' not in self._headers):
                hasher = hashlib.md5()
                for part in self._write_buffer:
                    hasher.update(part)
                etag = '"{}"'.format(hasher.hexdigest())
                self.set_header('Etag', etag)
                inm = self.request.headers.get('If-None-Match')
                if inm and inm.find(etag) != -1:
                    self._write_buffer = []
                    self.status_code = 304
            if self._status_code == 304:
                assert not self._write_buffer, 'Cannot send body with 304'
                self._clear_headers_for_304()
            elif 'Content-Length' not in self._headers:
                content_length = sum(len(part) for part in self._write_buffer)
                self.set_header('Content-Length', content_length)

        self.flush()
        if no_keep_alive:
            self.connection.no_keep_alive = True
        self.connection.finish()
        self._finished = True

    def _generate_headers(self):
        lines = [' '.join((self.request.version, str(self._status_code), httplib.responses[self._status_code]))]
        lines.extend(['{}: {}'.format(n, v) for n, v in self._headers.items()])
        for cookie in self._cookies.values():
            LOGGER.debug(to_str('Set-Cookie: ' + cookie.OutputString(None)))
            lines.append(to_str('Set-Cookie: ' + cookie.OutputString(None)))
        return '\r\n'.join(lines) + '\r\n\r\n'

    def disable_cache(self):
        self.set_header('Pragma', 'no-cache')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Expires', 'Thu, 01 Jan 1970 00:00:01 GMT')  # epoch
