from __future__ import unicode_literals, print_function, division
import httplib
from veil.frontend.web.tornado import *
from sandal.test import TestCase
from ..browser import Browser

class BrowserTest(TestCase):
    def test_ok(self):
        def handler():
            get_current_http_response().write('hello')
            get_current_http_response().finish()

        http_server = start_test_http_server(handler=handler)
        browser = Browser('localhost:{}'.format(http_server.port))
        with browser.get('/'):
            self.assertEqual('hello', browser.page.response_text)

    def test_forbidden(self):
        def handler():
            raise HTTPError(httplib.FORBIDDEN)

        http_server = start_test_http_server(handler=handler)
        browser = Browser('localhost:{}'.format(http_server.port))
        with browser.get('/', expected_status_code=httplib.FORBIDDEN):
            self.assertEqual(httplib.FORBIDDEN, browser.page.status_code)

    def test_found(self):
        def handler():
            if '/hello' == get_current_http_request().path:
                get_current_http_response().write('hello')
                get_current_http_response().finish()
            else:
                redirect_to('/hello')

        http_server = start_test_http_server(handler=handler)
        browser = Browser('localhost:{}'.format(http_server.port))
        with browser.get('/', expected_status_code=httplib.FOUND):
            self.assertEqual('hello', browser.follow_redirect().response_text)

    def test_cookie(self):
        def handler():
            val = int(get_cookie(name='val', default='0'))
            get_current_http_response().write(unicode(val))
            val += 1
            set_cookie(name='val', value=unicode(val))
            get_current_http_response().finish()

        http_server = start_test_http_server(handler=handler)
        browser = Browser('localhost:{}'.format(http_server.port))
        self.assertEqual('0', browser.get('/').response_text)
        self.assertEqual('1', browser.get('/').response_text)
        self.assertEqual('2', browser.get('/').response_text)

