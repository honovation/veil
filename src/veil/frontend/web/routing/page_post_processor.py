from __future__ import unicode_literals, print_function, division
from veil.development.test import *

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


def post_process_page(route_handler, data):
    for page_post_processor in page_post_processors:
        data = page_post_processor(route_handler, data)
    return data