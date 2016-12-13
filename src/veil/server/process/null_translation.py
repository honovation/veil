# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import sys
from gettext import NullTranslations

from veil.development.test import *
from veil.model.event import *
from .process_event import EVENT_PROCESS_SETUP


@event(EVENT_PROCESS_SETUP)
@test_hook
def install_null_translation():
    def clean_up():
        del sys.modules['__builtin__'].__dict__['_']

    executing_test = get_executing_test(optional=True)
    if executing_test:
        executing_test.addCleanup(clean_up)
    NullTranslations().install(unicode=True)
