from __future__ import unicode_literals, print_function, division
import functools
import sys
from logging import getLogger
from inspect import getargspec
import traceback
from markupsafe import Markup
from veil.development.test import *
from veil.frontend.encoding import *

original_page_post_processors = None
page_post_processors = []

@test_hook
def remember_original_page_post_processors():
    get_executing_test().addCleanup(reset_page_post_processors)
    global original_page_post_processors
    if not original_page_post_processors:
        original_page_post_processors = list(page_post_processors)


def reset_page_post_processors():
    global page_post_processors
    page_post_processors = []
    if original_page_post_processors:
        page_post_processors.extend(original_page_post_processors)


def register_page_post_processor(page_post_processor):
    page_post_processors.append(page_post_processor)