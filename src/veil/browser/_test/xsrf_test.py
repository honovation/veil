from __future__ import unicode_literals, print_function, division
import httplib
from veil.http import get_current_http_response, xsrf_token
from sandal.fixture import fixtures
from sandal.fixture import UsingFixture

class XsrfTest(UsingFixture):
    def test_form_submission(self):
        def handler():
            get_current_http_response().write(xsrf_token())
            get_current_http_response().finish()
        browser = fixtures.start_browser(http_server=fixtures.start_http_server(handler=handler))
        browser.post('/', auto_xsrf=False, expected_status_code=httplib.FORBIDDEN)
        with browser.get('/'):
            _xsrf = browser.page.response_text
        browser.post('/', auto_xsrf=False, arguments={'_xsrf':_xsrf})
        browser.post('/', auto_xsrf=False, arguments={'_xsrf':'123'}, expected_status_code=httplib.FORBIDDEN)

    def test_ajax(self):
        def handler():
            get_current_http_response().write('hello')
            get_current_http_response().finish()
        browser = fixtures.start_browser(http_server=fixtures.start_http_server(handler=handler))
        self.assertNotIn('_xsrf', browser.cookies)
        self.assertEqual('hello', browser.get('/').response_text)
        self.assertIsNotNone(browser.cookies['_xsrf'].value)
        self.assertEqual('hello', browser.post(
            '/', auto_xsrf=False, headers={'X-XSRF': browser.cookies['_xsrf'].value}).response_text)


