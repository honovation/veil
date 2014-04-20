from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .link_element import process_link_elements


class LinkElementTest(TestCase):
    def test_non_stylesheet(self):
        html, css_elements = process_link_elements('<link rel="alternate" href="/test.html"/>')
        self.assertEqual('<link rel="alternate" href="/test.html"/>', html)
        self.assertEqual([], css_elements)

    def test_closing(self):
        html, css_elements = process_link_elements('<link rel="stylesheet" href="/test.css"/>')
        self.assertEqual('', html)
        self.assertEqual(['<link rel="stylesheet" href="/test.css"/>'], css_elements)

    def test_opening(self):
        html, css_elements = process_link_elements('<link rel="stylesheet" href="/test.css"></link>')
        self.assertEqual('', html)
        self.assertEqual(['<link rel="stylesheet" href="/test.css"></link>'], css_elements)

    def test_tail_head_kept(self):
        html, css_elements = process_link_elements('''
            a
            <link rel="stylesheet" href="/test1.css"></link>
            b
            <link rel="stylesheet" href="/test2.css"></link>
            c
            ''')
        self.assertEqual('abc', html.replace('\n', '').replace(' ', ''))
        self.assertEqual(['<link rel="stylesheet" href="/test1.css"></link>', '<link rel="stylesheet" href="/test2.css"></link>'], css_elements)
