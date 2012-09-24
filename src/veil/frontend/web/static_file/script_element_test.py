from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .script_element import process_script_elements


class ScriptElementTest(TestCase):
    def test_empty(self):
        html = '<script></script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual([''], js_texts)

    def test_internal_text(self):
        html = '<script>hello</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual(['hello'], js_texts)

    def test_new_line_in_text(self):
        html = '<script>hel\nlo</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual(['hel\nlo'], js_texts)

    def test_xml_in_text(self):
        html = '<script><b>hello</b></script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual(['<b>hello</b>'], js_texts)

    def test_two_script_texts(self):
        html = '<script>a</script><script>\nb</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual(['a', '\nb'], js_texts)

    def test_head_tail_kept(self):
        html = 'a<script></script>b'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('ab', html)
        self.assertEqual([], script_elements)
        self.assertEqual([''], js_texts)

    def test_text_plain_skipped(self):
        html = '<script type="text/plain">abc</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('<script type="text/plain">abc</script>', html)
        self.assertEqual([], script_elements)
        self.assertEqual([], js_texts)

    def test_text_javascript_processed(self):
        html = '<script type="text/javascript">abc</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual(['abc'], js_texts)

    def test_upper_case(self):
        html = '<SCRIPT></script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual([], script_elements)
        self.assertEqual([''], js_texts)

    def test_external_urls(self):
        html = '<script type="text/javascript" src="/test.js">abc</script>'
        html, script_elements, js_texts = process_script_elements(html)
        self.assertEqual('', html)
        self.assertEqual(['<script type="text/javascript" src="/test.js">abc</script>'], script_elements)
        self.assertEqual([], js_texts)








