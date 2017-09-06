# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from .new_ad_law import get_new_ad_law_matched_words


class NewADLawTest(TestCase):
    def test_empty_words_match(self):
        self.assertEqual([], get_new_ad_law_matched_words([]))

    def test_words_match(self):
        self.assertEqual({'最好', '最'}, set(get_new_ad_law_matched_words(['最好', '东半球'])))