from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .link_element import process_link_elements


class LinkElementTest(TestCase):
    def test_closing(self):
        html, css_urls = process_link_elements('<link rel="stylesheet" href="/test.css"/>')
        self.assertEqual('', html)
        self.assertEqual(['/test.css'], css_urls)

    def test_opening(self):
        html, css_urls = process_link_elements('<link rel="stylesheet" href="/test.css"></link>')
        self.assertEqual('', html)
        self.assertEqual(['/test.css'], css_urls)

    def test_tail_head_kept(self):
        html, css_urls = process_link_elements(
            """
            a
            <link rel="stylesheet" href="/test1.css"></link>
            b
            <link rel="stylesheet" href="/test2.css"></link>
            c
            """)
        self.assertEqual('abc', html.replace('\n', '').replace(' ', ''))
        self.assertEqual(['/test1.css', '/test2.css'], css_urls)
