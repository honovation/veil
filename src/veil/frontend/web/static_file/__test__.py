from __future__ import unicode_literals, print_function, division
import os
import tempfile
from veil.utility.path import *
from veil.environment.setting import *
from veil.development.test import TestCase
from .static_file import process_javascript_and_stylesheet_tags

class ProcessJavascriptAndStylesheetTagsTest(TestCase):
    def setUp(self):
        super(ProcessJavascriptAndStylesheetTagsTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        update_options({
            'website': {
                'external_static_files_directory': os.path.dirname(__file__),
                'inline_static_files_directory': self.temp_dir
            }
        })

    def test_no_tag(self):
        self.assertEqual('', process_javascript_and_stylesheet_tags(None, ''))
        self.assertEqual('<html><body></body></html>', process_javascript_and_stylesheet_tags(
            None, '<html><body/></html>'))
        self.assertEqual(
            '<p>a<span class="test">b</span>c</p>',
            process_javascript_and_stylesheet_tags(None, '<p>a<span class="test">b</span>c</p>'))

    def test_javascript_tag_relocated_before_body_end(self):
        processed_html = process_javascript_and_stylesheet_tags(None,
            """
            <html>
            <body>
            <script src="abc"></script>
            <p/>
            </body>
            </html>
            """).strip()
        self.assertEqual(
            """
            <html><body>
            <p></p>
            <script src="abc"></script></body></html>
            """.strip(), processed_html)

    def test_stylesheet_tag_relocated_before_head_end(self):
        processed_html = process_javascript_and_stylesheet_tags(None,
            """
            <html>
            <head>
            <title>hello</title>
            </head>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"/>
            </html>
            """
        ).strip()
        self.assertEqual(
            """
            <html><head><title>hello</title><link rel="stylesheet" type="text/css" media="screen" href="a.css"></head></html>
            """.strip(), processed_html)

    def test_inline_script(self):
        def test_page():
            return """
            <script>test</script>
            <script>test</script>
            <script>test2</script>
            """

        processed_html = process_javascript_and_stylesheet_tags(test_page, test_page()).strip()
        self.assertEqual(
            """
            <script src="/static/v-0f0e03094c8ea974cf442bdc461b7b14/test.js" type="text/javascript"></script>
            """.strip(), processed_html)
        self.assertEqual('test\ntest2', (self.temp_dir / '0f0e03094c8ea974cf442bdc461b7b14').text())

    def test_inline_style(self):
        def test_page():
            return """
            <style>test</style>
            <style>test2</style>
            <style>test2</style>
            """
        processed_html = process_javascript_and_stylesheet_tags(test_page, test_page()).strip()
        self.assertEqual(
            """
            <link href="/static/v-0f0e03094c8ea974cf442bdc461b7b14/test.css" type="text/css" rel="stylesheet">
            """.strip(), processed_html)
        self.assertEqual('test\ntest2', (self.temp_dir / '0f0e03094c8ea974cf442bdc461b7b14').text())










