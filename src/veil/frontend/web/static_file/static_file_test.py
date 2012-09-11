from __future__ import unicode_literals, print_function, division
import os
import tempfile
from veil.utility.path import *
from veil.development.test import TestCase
from .static_file import set_inline_static_files_directory
from .static_file import set_external_static_files_directory
from .static_file import process_javascript_and_stylesheet_tags
from .static_file import clear_script_elements_processors

class ProcessJavascriptAndStylesheetTagsTest(TestCase):
    def setUp(self):
        super(ProcessJavascriptAndStylesheetTagsTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        set_external_static_files_directory(os.path.dirname(__file__))
        set_inline_static_files_directory(self.temp_dir)
        clear_script_elements_processors()

    def test_no_tag(self):
        self.assertEqual('', unicode(process_javascript_and_stylesheet_tags(None, '')))
        self.assertEqual('<html><body></body></html>', unicode(process_javascript_and_stylesheet_tags(
            None, '<html><body/></html>')))
        self.assertEqual(
            '<p>a<span class="test">b</span>c</p>',
            unicode(process_javascript_and_stylesheet_tags(None, '<p>a<span class="test">b</span>c</p>')))

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
            <html>
            <body>
            <p></p>
            <script src="abc"></script>
            </body>
            </html>
            """.strip(), unicode(processed_html))

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
            <html>
            <head>
            <title>hello</title>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"></link>
            </head>
            </html>
            """.strip(), unicode(processed_html))

    def test_inline_script(self):
        def test_page():
            return """
            <script>test</script>
            <script>test</script>
            <script>test2</script>
            """

        processed_html = unicode(process_javascript_and_stylesheet_tags(test_page, test_page()).strip())
        self.assertEqual(
            """
            <script src="/static/v-bde00465b10c6f9c285cec1f03fe311e/test.js" type="text/javascript"></script>
            """.strip(), processed_html)
        self.assertIn('test2', (self.temp_dir / 'bde00465b10c6f9c285cec1f03fe311e').text())

    def test_inline_style(self):
        def test_page():
            return """
            <style>test</style>
            <style>test2</style>
            <style>test2</style>
            """
        processed_html = unicode(process_javascript_and_stylesheet_tags(test_page, test_page()).strip())
        self.assertEqual(
            """
            <link href="/static/v-0f0e03094c8ea974cf442bdc461b7b14/test.css" rel="stylesheet" type="text/css"></link>
            """.strip(), processed_html)
        self.assertEqual('test\ntest2', (self.temp_dir / '0f0e03094c8ea974cf442bdc461b7b14').text())










