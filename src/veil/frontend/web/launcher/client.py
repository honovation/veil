from __future__ import unicode_literals, print_function, division
import cookielib
import httplib
import threading
import urllib
import urllib2
from .launcher import start_test_website
from veil.frontend.web.tornado import *

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


    def __enter__(self):
        threading.Thread(target=self.io_loop_executor.execute).start()
        return self


    def __exit__(self, type, value, traceback):
        if value:
            self.io_loop_executor.stop(failure=(type, value, traceback))
        else:
            self.io_loop_executor.stop()


class SilentHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    handler_order = 1000  # after all other processing

    def http_response(self, request, response):
        return response

    https_response = http_response
