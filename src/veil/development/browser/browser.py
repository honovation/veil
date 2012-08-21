from __future__ import unicode_literals, print_function, division
import functools
import logging
import threading
import lxml.html
import os.path
import spynner
from veil.utility.path import *
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

    @route('POST', '/-test/fail', website=website)
    def fail_test():
        get_executing_test().error = get_http_argument('message')

    @route('POST', '/-test/log', website=website)
    def log_from_test():
        LOGGER.info(get_http_argument('message'))

    @route('GET', '/-test/veil-test.js', website=website)
    def veil_test_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'veil-test.js').text()

    register_page_post_processor(lambda page_handler, html: inject_page_interaction(html))
    start_test_website(website)
    url = 'http://{}{}'.format(get_website_option(website, 'domain'), url)
    threading.Thread(target=lambda: require_io_loop_executor().execute(timeout=timeout)).start()
    threading.Thread(target=interact_with_pages).start()
    start_browser(url, visible=visible)


def start_browser(url, visible):
    test = get_executing_test()
    test.browser = spynner.Browser(debug_level=spynner.DEBUG)
    test.addCleanup(stop_browser)
    if visible:
        test.browser.show(maximized=False)
    try:
        test.browser.load(url)
    except:
        raise
    try:
        while test.browser:
            message = getattr(test, 'error', None)
            if message is None:
                test.browser._events_loop()
            else:
                stop_browser()
                require_io_loop_executor().stop(message)
                test.fail(message)
    except:
        raise


def stop_browser():
    browser = get_executing_test().browser
    if browser:
        get_executing_test().browser = None
        browser.close()


def inject_page_interaction(html):
    request = get_current_http_request()
    if 'XMLHttpRequest' == request.headers.get('X-Requested-With', None):
        return html
    if request.path.startswith('/-test/'):
        return html
    page_interaction_requested.release()
    page_interaction_ready.acquire()
    test = get_executing_test()
    if getattr(test, 'page_interaction_index', None):
        test.page_interaction_index += 1
    else:
        test.page_interaction_index = 1
    fragment = lxml.html.document_fromstring(html)
    script = fragment.makeelement(
        'script', attrib={
            'type': 'text/javascript',
            'src': '/-test/veil-test.js'
        })
    script.text = ' '
    fragment.find('body').append(script)
    script = fragment.makeelement(
        'script', attrib={'type': 'text/javascript'})
    script.text = current_page_interaction
    fragment.find('body').append(script)
    return lxml.html.tostring(fragment, method='xml')


def interact_with_page(page_interaction):
    global current_page_interaction
    page_interaction_requested.acquire()
    current_page_interaction = page_interaction
    page_interaction_ready.release()