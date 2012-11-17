# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.development.test import *

def check_live_document():
    for doc in (VEIL_HOME / '文档').walkfiles('*.py'):
        exec(compile(doc.text(), doc, 'exec'))
        tear_down_fake_test()