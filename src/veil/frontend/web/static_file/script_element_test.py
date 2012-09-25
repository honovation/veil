from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .script_element import process_script_elements


class ScriptElementTest(TestCase):
    def test_empty(self):
        html = '<script></script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual([''], js_texts)

    def test_internal_text(self):
        html = '<script>hello</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual(['hello'], js_texts)

    def test_new_line_in_text(self):
        html = '<script>hel\nlo</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual(['hel\nlo'], js_texts)

    def test_xml_in_text(self):
        html = '<script><b>hello</b></script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual(['<b>hello</b>'], js_texts)

    def test_two_script_texts(self):
        html = '<script>a</script><script>\nb</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual(['a', '\nb'], js_texts)

    def test_head_tail_kept(self):
        html = 'a<script></script>b'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('ab', html)
        self.assertEqual([], js_urls)
        self.assertEqual([''], js_texts)

    def test_text_plain_skipped(self):
        html = '<script type="text/plain">abc</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('<script type="text/plain">abc</script>', html)
        self.assertEqual([], js_urls)
        self.assertEqual([], js_texts)

    def test_text_javascript_processed(self):
        html = '<script type="text/javascript">abc</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual(['abc'], js_texts)

    def test_upper_case(self):
        html = '<SCRIPT></script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], js_urls)
        self.assertEqual([''], js_texts)

    def test_external_urls(self):
        html = '<script type="text/javascript" src="/test.js">abc</script>'
        html, js_urls, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual(['/test.js'], js_urls)
        self.assertEqual([], js_texts)








