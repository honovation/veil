# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import importlib
import inspect
import os

from veil.utility.encoding import *

new_ad_law_words = None


def get_new_ad_law_matched_words(words):
    words = [to_unicode(w) for w in words]
    global new_ad_law_words
    if new_ad_law_words is None:
        load_new_ad_law_words()
    matched = []
    for w in new_ad_law_words:
        for word in words:
            if w in word:
                matched.append(w)
    return matched


def load_new_ad_law_words():
    module_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    words_path = '{}/words'.format(os.path.dirname(os.path.abspath(importlib.import_module(module_name).__file__)))
    with open(words_path) as f:
        lines = f.readlines()
    lines = [to_unicode(line.strip()) for line in lines if line.strip()]
    global new_ad_law_words
    new_ad_law_words = lines
