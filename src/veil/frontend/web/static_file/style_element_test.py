from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .style_element import process_style_elements


class StyleElementTest(TestCase):
    def test_empty(self):
        html, css_texts = process_style_elements('<style></style>')
        self.assertEqual('', html)
        self.assertEqual([''], css_texts)

    def test_non_empty(self):
        html, css_texts = process_style_elements('<style>abc</style>')
        self.assertEqual('', html)
        self.assertEqual(['abc'], css_texts)