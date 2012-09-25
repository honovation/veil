from __future__ import unicode_literals, print_function, division
import tempfile
import lxml.html
import lxml.etree
from veil.utility.path import *
from veil.development.test import *
from .static_file import set_inline_static_files_directory
from .static_file import process_javascript
from .static_file import process_stylesheet

class ProcessJavascriptTest(TestCase):
    def setUp(self):
        super(ProcessJavascriptTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        set_inline_static_files_directory(self.temp_dir)

    def test_nothing_to_process(self):
        self.assertEqual('', unicode(process_javascript(None, '')))
        self.assertEqual('<html><body/></html>', unicode(process_javascript(
            None, '<html><body/></html>')))
        self.assertEqual(
            '<p>a<span class="test">b</span>c</p>',
            unicode(process_javascript(None, '<p>a<span class="test">b</span>c</p>')))

    def test_script_element_relocated_before_body_end(self):
        processed_html = process_javascript(None,
            """
            <html>
            <body>
            <script src="abc"></script>
            <p/>
            </body>
            </html>
            """).strip()
        doc = lxml.etree.fromstring(processed_html)
        script_element = doc[0][1]
        self.assertEqual('abc', script_element.attrib['src'])
        processed_html = process_javascript(None,
            """
            <html>
            <BODY>
            <script src="abc"></script>
            <p/>
            </BODY>
            </html>
            """).strip()
        doc = lxml.etree.fromstring(processed_html)
        script_element = doc[0][1]
        self.assertEqual('abc', script_element.attrib['src'])

    def test_script_element_relocated_even_body_end_not_found(self):
        processed_html = process_javascript(None, '<script src="abc"></script>')
        doc = lxml.etree.fromstring(processed_html)
        self.assertEqual('abc', doc.attrib['src'])

    def test_inline_javascript(self):
        def test_page():
            return """
            <script>test</script>
            <script>test</script>
            <script>test2</script>
            """

        processed_html = unicode(process_javascript(test_page, test_page()).strip())
        doc = lxml.etree.fromstring(processed_html)
        self.assertEqual('/static/v-4749495e5842d5f8f6a4f54fb596a9dd/test.js', doc.attrib['src'])
        self.assertIn('test2', (self.temp_dir / '4749495e5842d5f8f6a4f54fb596a9dd').text())


class ProcessStylesheetTest(TestCase):
    def setUp(self):
        super(ProcessStylesheetTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        set_inline_static_files_directory(self.temp_dir)

    def test_link_element_relocated_before_head_end(self):
        processed_html = process_stylesheet(None,
            """
            <html>
            <head>
            <title>hello</title>
            </head>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"/>
            </html>
            """
        ).strip()
        doc = lxml.html.document_fromstring(processed_html)
        link_element = doc[0][1]
        self.assertEqual('a.css', link_element.attrib['href'])

    def test_link_element_relocated_even_head_end_not_found(self):
        processed_html = process_stylesheet(
            None, '<link rel="stylesheet" type="text/css" media="screen" href="a.css"/>')
        doc = lxml.etree.fromstring(processed_html)
        self.assertEqual('a.css', doc.attrib['href'])

    def test_inline_stylesheet(self):
        def test_page():
            return """
            <style>test</style>
            <style>test2</style>
            <style>test2</style>
            """

        processed_html = unicode(process_stylesheet(test_page, test_page()).strip())
        doc = lxml.etree.fromstring(processed_html)
        self.assertEqual('/static/v-d4d47e28f5e98547ee210c3efe99cc2e/test.css', doc.attrib['href'])
        self.assertEqual('test\ntest2', (self.temp_dir / 'd4d47e28f5e98547ee210c3efe99cc2e').text())










