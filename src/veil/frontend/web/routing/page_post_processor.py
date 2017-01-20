from __future__ import unicode_literals, print_function, division
import logging
import copy
from veil.development.test import *
from veil.frontend.web.tornado import *

LOGGER = logging.getLogger(__name__)

original_processor_type2processor_list = {}
PAGE_PROCESSOR_TYPE_NORMAL = 1
PAGE_PROCESSOR_TYPE_JS = 2
PAGE_PROCESSOR_TYPE_CSS = 3
PROCESSOR_TYPE2RPOCESSOR_LIST = {
    PAGE_PROCESSOR_TYPE_NORMAL: [],
    PAGE_PROCESSOR_TYPE_JS: [],
    PAGE_PROCESSOR_TYPE_CSS: []
}

TAG_NO_POST_PROCESS = 'no-post-process'
TAG_NO_JS_POST_PROCESS = 'no-js-post-process'
TAG_NO_CSS_POST_PROCESS = 'no-css-post-process'


@test_hook
def remember_original_page_post_processors():
    get_executing_test().addCleanup(reset_page_post_processors)
    global original_processor_type2processor_list
    if not original_processor_type2processor_list:
        original_processor_type2processor_list = copy.deepcopy(PROCESSOR_TYPE2RPOCESSOR_LIST)


def reset_page_post_processors():
    global PROCESSOR_TYPE2RPOCESSOR_LIST
    PROCESSOR_TYPE2RPOCESSOR_LIST = copy.deepcopy(original_processor_type2processor_list)


def register_page_post_processor(page_post_processor, insert_to_head=False, type=PAGE_PROCESSOR_TYPE_NORMAL):
    processor_list = PROCESSOR_TYPE2RPOCESSOR_LIST[type]
    if insert_to_head:
        processor_list.insert(0, page_post_processor)
    else:
        processor_list.append(page_post_processor)


def register_page_js_post_processor(js_post_processor, insert_to_head=False):
    register_page_post_processor(js_post_processor, insert_to_head=insert_to_head, type=PAGE_PROCESSOR_TYPE_JS)


def register_page_css_post_processor(css_post_processor, insert_to_head=False):
    register_page_post_processor(css_post_processor, insert_to_head=insert_to_head, type=PAGE_PROCESSOR_TYPE_CSS)


def post_process_page(route_handler, data):
    route_tags = get_current_http_request().route.tags
    if TAG_NO_POST_PROCESS in route_tags:
        return data
    for page_post_processor in PROCESSOR_TYPE2RPOCESSOR_LIST[PAGE_PROCESSOR_TYPE_NORMAL]:
        data = page_post_processor(route_handler, data)
    if TAG_NO_JS_POST_PROCESS not in route_tags:
        for js_post_processor in PROCESSOR_TYPE2RPOCESSOR_LIST[PAGE_PROCESSOR_TYPE_JS]:
            data = js_post_processor(route_handler, data)
    if TAG_NO_CSS_POST_PROCESS not in route_tags:
        for css_post_processor in PROCESSOR_TYPE2RPOCESSOR_LIST[PAGE_PROCESSOR_TYPE_CSS]:
            data = css_post_processor(route_handler, data)
    return data
