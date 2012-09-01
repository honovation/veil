from __future__ import unicode_literals, print_function, division
import httplib
import urllib2
from veil.frontend.web.routing import *
from veil.frontend.web.xsrf import *
from veil.development.test import *
from veil.environment.setting import *
from .client import start_website_and_client

class XsrfTest(TestCase):
    def setUp(self):
        super(XsrfTest, self).setUp()
        update_options({
            'veil': {
                'test_website': {
                    'prevents_xsrf': True
                }
            }
        })

    def test_form_submission(self):
        @route('GET', '/', website='test')
        def show_xsrf_token():
            return xsrf_token()

        @route('POST', '/', website='test')
        def dummy():
            pass

        client = start_website_and_client('test')
        with client:
            client.post('/', expects=httplib.FORBIDDEN)
            client.post('/', form={'_xsrf': client.get('/').read()})
            client.post('/', form={'_xsrf': '123'}, expects=httplib.FORBIDDEN)

    def test_ajax(self):
        @route('GET', '/', website='test')
        def say_hello():
            return 'hello'

        @route('POST', '/', website='test')
        def say_yes():
            return 'yes'

        client = start_website_and_client('test')
        with client:
            self.assertNotIn('_xsrf', client.cookies)
            self.assertEqual('hello', client.get('/').read())
            _xsrf = client.cookies['_xsrf'].value
            self.assertIsNotNone(_xsrf)
            self.assertEqual('yes', client.post('/', headers={'X-XSRF': _xsrf}).read())


