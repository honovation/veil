from __future__ import unicode_literals, print_function, division
import httplib
from veil.development.test import *
from .client import start_website_and_client
from .routing import *
from .website_installer import override_website_config

class XsrfTest(TestCase):
    def setUp(self):
        super(XsrfTest, self).setUp()
        override_website_config('test', domain='', domain_port=0, start_port=4999, locale='', master_template_directory='', prevents_xsrf=True,
            recalculates_static_file_hash=True, clears_template_cache=True)

    def test_form_submission(self):
        @route('POST', '/', website='test')
        def dummy():
            pass

        client = start_website_and_client('test')
        with client:
            client.post('/', expects=httplib.FORBIDDEN)
            client.set_cookie('_xsrf', 'abc')
            client.post('/', form={'_xsrf': 'abc'})
            client.post('/', form={'_xsrf': '123'}, expects=httplib.FORBIDDEN)

    def test_ajax(self):
        @route('POST', '/', website='test')
        def say_yes():
            return 'yes'

        client = start_website_and_client('test')
        with client:
            client.set_cookie('_xsrf', 'abc')
            self.assertIn('yes', client.post('/', headers={'X-XSRF': 'abc'}).read())


