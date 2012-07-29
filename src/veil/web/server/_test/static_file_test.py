from __future__ import unicode_literals, print_function, division
import tempfile
import os.path
from sandal.fixture import fixtures
from sandal.template import get_template
from sandal.fixture import UsingFixture
from veil.environment.runtime import init_options
from veil.environment.runtime import reset_options
from sandal.path import *
from ..routing import route

class StaticFileModuleSmokeTest(UsingFixture):
    def setUp(self):
        super(StaticFileModuleSmokeTest, self).setUp()
        self.temp_dir = path(tempfile.gettempdir())
        init_options({
            'website': {
                'external_static_files_directory': os.path.dirname(__file__),
                'inline_static_files_directory': self.temp_dir
            }
        })

    def tearDown(self):
        super(StaticFileModuleSmokeTest, self).tearDown()
        reset_options()

    def test_static_url(self):
        @route('GET', '/using_static_url', website='test')
        def using_static_url():
            return get_template(template_source="{{ static_url('hello.js') }}").render()
        
        browser = fixtures.start_website_and_browser('test')
        js_url = browser.get('/using_static_url').response_text
        self.assertIn('/static/hello.js', js_url)

    def test_script_tag_moved(self):
        @route('GET', '/one_script_tag', website='test')
        def one_script_tag():
            return '<script></script>test'
        browser = fixtures.start_website_and_browser('test')
        self.assertEqual('test<script></script>', browser.get('/one_script_tag').response_text)

    def test_script_tag_combined(self):
        @route('GET', '/two_script_tags', website='test')
        def two_script_tags():
            return 'test<script></script><script></script>'
        browser = fixtures.start_website_and_browser('test')
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

        browser = fixtures.start_website_and_browser('test')
        with browser.get('/inline_javascript'):
            file_name = browser.q('script').attr('src').replace('/static/v-', '')
            self.assertEqual('Hello!', (self.temp_dir / file_name).text().strip())







