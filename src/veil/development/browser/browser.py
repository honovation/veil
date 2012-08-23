from __future__ import unicode_literals, print_function, division
import logging
import threading
import time
import signal
import lxml.html
import os.path
import spynner
import selenium.webdriver
import os
from veil.utility.path import *
from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web import *
from veil.backend.shell import *

LOGGER = logging.getLogger(__name__)

def start_website_and_browser(website, path, page_interactions, timeout=60, browser='spynner'):
    @route('POST', '/-test/stop', website=website)
    def _stop_test():
        stop_test()

    @route('POST', '/-test/fail', website=website)
    def fail_test():
        message = get_http_argument('message')
        LOGGER.error(message)
        get_executing_test().error = message

    @route('POST', '/-test/log', website=website)
    def log_from_test():
        LOGGER.info(get_http_argument('message'))

    @route('GET', '/-test/veil-test.js', website=website)
    def veil_test_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'veil-test.js').text()

    @route('GET', '/-test/jquery.js', website=website)
    def jquery_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'jquery.js').text()

    @route('GET', '/-test/jquery-cookie.js', website=website)
    def jquery_cookie_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'jquery-cookie.js').text()

    @route('GET', '/-test/veil.js', website=website)
    def veil_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'veil.js').text()

    get_executing_test().browser_type = browser
    page_interactions = list(reversed(page_interactions))
    register_page_post_processor(lambda page_handler, html: inject_page_interaction(html, page_interactions))
    http_server = start_test_website(website)
    domain = get_website_option(website, 'domain')
    if domain:
        url = 'http://{}{}'.format(domain, path)
    else:
        url = 'http://{}:{}{}'.format(http_server.host, http_server.port, path)
    threading.Thread(target=lambda: require_io_loop_executor().execute(timeout=timeout)).start()
    start_browser(url)


def start_browser(url):
    test = get_executing_test()
    test.addCleanup(stop_browser)
    if 'spynner' == test.browser_type:
        start_spynner_browser(url)
    elif 'chrome' == test.browser_type:
        start_chrome_browser(url)
    else:
        raise NotImplementedError('unknown browser type: {}'.format(test.browser_type))


def start_chrome_browser(url):
    test = get_executing_test()
    old_cwd = os.getcwd()
    os.chdir('/tmp')
    test.chrome_browser = selenium.webdriver.Chrome()
    os.chdir(old_cwd)
    test.chrome_browser.get(url)
    while test.chrome_browser:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            stop_test()
        check_is_test_failed(test)


def start_spynner_browser(url, visible=False):
    test = get_executing_test()
    test.spynner_browser = spynner.Browser(debug_level=spynner.DEBUG)
    if visible:
        test.spynner_browser.show(maximized=False)
    try:
        test.spynner_browser.load(url)
    except:
        pass
    while test.spynner_browser:
        try:
            test.spynner_browser._events_loop()
        except KeyboardInterrupt:
            stop_test()
        check_is_test_failed(test)


def check_is_test_failed(test):
    message = getattr(test, 'error', None)
    if message is not None:
        stop_browser()
        require_io_loop_executor().stop(message)
        test.fail(message)


def stop_test():
    require_io_loop_executor().stop()
    stop_browser()


def stop_browser():
    test = get_executing_test()
    if 'spynner' == test.browser_type:
        stop_spynner_browser()
    elif 'chrome' == test.browser_type:
        stop_chrome_browser()
    else:
        raise NotImplementedError('unknown browser type: {}'.format(test.browser_type))


def stop_chrome_browser():
    test = get_executing_test()
    browser = test.chrome_browser
    if browser:
        test.chrome_browser = None
        browser.close()


def stop_spynner_browser():
    test = get_executing_test()
    browser = test.spynner_browser
    if browser:
        test.spynner_browser = None
        browser.close()


def inject_page_interaction(html, page_interactions):
    request = get_current_http_request()
    if 'XMLHttpRequest' == request.headers.get('X-Requested-With', None):
        return html
    if request.path.startswith('/-test/'):
        return html
    if not page_interactions:
        return html
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
    script.text =\
    """
    $(document).ready(function() {
        %s
    });
    """ % page_interactions.pop()
    fragment.find('body').append(script)
    return lxml.html.tostring(fragment, method='xml')