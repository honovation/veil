from __future__ import unicode_literals, print_function, division
import cookielib
import httplib
import urllib
import urllib2
from .website_launcher import start_test_website
from .tornado import *

def start_website_and_client(website):
    http_server = start_test_website(website)
    return WebClient(http_server.host, http_server.port, require_io_loop_executor())


class WebClient(object):
    def __init__(self, host, port, io_loop_executor=None):
        self.host = host
        self.port = port
        self.io_loop_executor = io_loop_executor
        self.cookie_jar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar), SilentHTTPErrorProcessor())

    def get(self, path, expects=httplib.OK):
        response = self.opener.open(self.to_url(path))
        assert expects == response.code, 'status code: {}'.format(response.code)
        return response

    def post(self, path, form=None, headers=None, expects=httplib.OK):
        form = form or {}
        headers = headers or {}
        request = urllib2.Request(self.to_url(path), data=urllib.urlencode(form), headers=headers)
        response = self.opener.open(request)
        assert expects == response.code, 'status code: {}'.format(response.code)
        return response

    def to_url(self, path):
        return 'http://{}:{}{}'.format(self.host, self.port, path)

    @property
    def cookies(self):
        return dict((cookie.name, cookie) for cookie in self.cookie_jar)

    def set_cookie(self, key, value):
        cookie = cookielib.Cookie(version=0, name=key, value=value, port=None, port_specified=False,
            domain=u'localhost.local', domain_specified=False, domain_initial_dot=False, path='/',
            path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None,
            rest={}, rfc2109=False)
        self.cookie_jar.set_cookie(cookie)


    def __enter__(self):
        self.io_loop_executor.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.io_loop_executor.__exit__(type, value, traceback)


class SilentHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    handler_order = 1000  # after all other processing

    def http_response(self, request, response):
        return response

    https_response = http_response
