from __future__ import unicode_literals, print_function, division
import httplib
from veil.frontend.web.routing import *
from veil.frontend.web.xsrf import *
from veil.frontend.web.launcher import *
from veil.development.test import TestCase
from ..browser import Browser

class XsrfTest(TestCase):
    def test_form_submission(self):
        @route('GET', '/', website='test')
        def show_xsrf_token():
            return xsrf_token()

        @route('POST', '/', website='test')
        def dummy():
            pass

        http_server = start_test_website('test', prevents_xsrf=True)
        browser = Browser('localhost:{}'.format(http_server.port))
        browser.post('/', auto_xsrf=False, expected_status_code=httplib.FORBIDDEN)
        with browser.get('/'):
            _xsrf = browser.page.response_text
        browser.post('/', auto_xsrf=False, arguments={'_xsrf': _xsrf})
        browser.post('/', auto_xsrf=False, arguments={'_xsrf': '123'}, expected_status_code=httplib.FORBIDDEN)

    def test_ajax(self):
        @route('GET', '/', website='test')
        def say_hello():
            return 'hello'

        @route('POST', '/', website='test')
        def say_yes():
            return 'yes'

        http_server = start_test_website('test', prevents_xsrf=True)
        browser = Browser('localhost:{}'.format(http_server.port))
        self.assertNotIn('_xsrf', browser.cookies)
        self.assertEqual('hello', browser.get('/').response_text)
        self.assertIsNotNone(browser.cookies['_xsrf'].value)
        self.assertEqual('yes', browser.post(
            '/', auto_xsrf=False, headers={'X-XSRF': browser.cookies['_xsrf'].value}).response_text)


