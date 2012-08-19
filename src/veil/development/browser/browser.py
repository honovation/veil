from __future__ import unicode_literals, print_function, division
import functools
import logging
import threading
import lxml.html
import spynner
from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web import *

current_page_interaction = None
page_interaction_requested = threading.Lock()
page_interaction_requested.acquire()
page_interaction_ready = threading.Lock()
page_interaction_ready.acquire()

LOGGER = logging.getLogger(__name__)

def browsing(website, url, **browsing_args):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return start_website_and_browser(website, url, lambda: func(*args, **kwargs), **browsing_args)

        return wrapper

    return decorator


def start_website_and_browser(website, url, interact_with_pages, timeout=60, visible=False):
    @route('POST', '/-test/stop', website=website)
    def stop_test():
        stop_browser()
        require_io_loop_executor().stop(get_http_arguments())

    register_page_post_processor(lambda page_handler, html: inject_page_interaction(html))
    server = start_test_website(website)
    url = 'http://{}:{}{}'.format(server.host, server.port, url)
    threading.Thread(target=lambda: require_io_loop_executor().execute(timeout=timeout)).start()
    threading.Thread(target=interact_with_pages).start()
    start_browser(url, visible=visible)


def start_browser(url, visible):
    test = get_executing_test()
    test.browser = spynner.Browser(debug_level=spynner.DEBUG)
    test.addCleanup(stop_browser)
    if visible:
        test.browser.show()
    test.browser.load(url)
    while test.browser:
        test.browser._events_loop()


def stop_browser():
    browser = get_executing_test().browser
    if browser:
        get_executing_test().browser = None
        browser.close()


def inject_page_interaction(html):
    page_interaction_requested.release()
    page_interaction_ready.acquire()
    test = get_executing_test()
    if getattr(test, 'page_interaction_index', None):
        test.page_interaction_index += 1
    else:
        test.page_interaction_index = 1
    fragment = lxml.html.document_fromstring(html)
    script = fragment.makeelement(
        'script', attrib={'type': 'text/javascript'})
    script.text = current_page_interaction
    fragment.find('body').append(script)
    return lxml.html.tostring(fragment)


def interact_with_page(page_interaction):
    global current_page_interaction
    page_interaction_requested.acquire()
    current_page_interaction = page_interaction
    page_interaction_ready.release()