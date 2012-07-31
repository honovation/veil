from __future__ import unicode_literals, print_function, division
import tempfile
import os.path
from veil.frontend.template import get_template
from sandal.test import TestCase
from veil.frontend.web.client import *
from veil.backend.path import *
from veil.environment.runtime import *
from ..routing import route

class StaticFileModuleSmokeTest(TestCase):
    def setUp(self):
        super(StaticFileModuleSmokeTest, self).setUp()
        self.temp_dir = path(tempfile.gettempdir())
        update_options({
            'website': {
                'external_static_files_directory': os.path.dirname(__file__),
                'inline_static_files_directory': self.temp_dir
            }
        })

    def test_static_url(self):
        @route('GET', '/using_static_url', website='test')
        def using_static_url():
            return get_template(template_source="{{ static_url('hello.js') }}").render()
        
        browser = start_website_and_browser('test')
        js_url = browser.get('/using_static_url').response_text
        self.assertIn('/static/hello.js', js_url)

    def test_script_tag_moved(self):
        @route('GET', '/one_script_tag', website='test')
        def one_script_tag():
            return '<script></script>test'
        browser = start_website_and_browser('test')
        self.assertEqual('test<script></script>', browser.get('/one_script_tag').response_text)

    def test_script_tag_combined(self):
        @route('GET', '/two_script_tags', website='test')
        def two_script_tags():
            return 'test<script></script><script></script>'
        browser = start_website_and_browser('test')
        self.assertEqual('test<script></script>', browser.get('/two_script_tags').response_text)

    def test_inline_javascript(self):
        @route('GET', '/inline_javascript', website='test')
        def inline_javascript():
            return get_template(template_source="""
            {% block inline_javascript %}
            <script>
            Hello!
            </script>{% endblock %}
            """).render()

        browser = start_website_and_browser('test')
        with browser.get('/inline_javascript'):
            file_name = browser.q('script').attr('src').replace('/static/v-', '')
            self.assertEqual('Hello!', (self.temp_dir / file_name).text().strip())







