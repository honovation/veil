from __future__ import unicode_literals, print_function, division
import functools
import logging
import threading
import time
import traceback
import os.path
import spynner
import selenium.webdriver
import os
import veil.component
from veil.utility.path import *
from veil.development.test import *
from veil.profile.web import *
from veil.frontend.web.static_file import *

LOGGER = logging.getLogger(__name__)

no_post_process_route = functools.partial(route, tags=(TAG_NO_POST_PROCESS,))

def start_website_and_browser(website, path, page_interactions, timeout=60, browser='spynner'):
    @no_post_process_route('POST', '/-test/stop', website=website, tags=())
    def stop_test():
        stop_browser()

    @no_post_process_route('POST', '/-test/fail', website=website)
    def fail_test():
        message = get_http_argument('message')
        LOGGER.error(message)
        get_executing_test().error = message

    @no_post_process_route('POST', '/-test/log', website=website)
    def log_from_test():
        LOGGER.info(get_http_argument('message'))

    @no_post_process_route('GET', '/-test/veil-test.js', website=website)
    def veil_test_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'veil-test.js').text()

    @no_post_process_route('GET', '/-test/jquery.js', website=website)
    def jquery_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'jquery.js').text()

    @no_post_process_route('GET', '/-test/jquery-cookie.js', website=website)
    def jquery_cookie_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'jquery-cookie.js').text()

    @no_post_process_route('GET', '/-test/veil.js', website=website)
    def veil_js():
        get_current_http_response().set_header('Content-Type', 'text/javascript; charset=utf-8')
        return (as_path(__file__).dirname() / 'veil.js').text()

    page_interactions = list(reversed(page_interactions))
    register_page_post_processor(lambda page_handler, html: inject_page_interaction(html, page_interactions))
    http_server = start_test_website(website)
    domain = get_website_option(website, 'domain')
    if domain:
        url = 'http://{}{}'.format(domain, path)
    else:
        url = 'http://{}:{}{}'.format(http_server.host, http_server.port, path)
    threading.Thread(target=lambda: execute_io_loop(timeout)).start()
    start_browser(url, browser)


def execute_io_loop(timeout):
    get_executing_test().addCleanup(require_io_loop_executor().stop)
    try:
        require_io_loop_executor().execute(timeout=timeout)
    except:
        get_executing_test().error = traceback.format_exc()
        raise


def start_browser(url, browser_type):
    if os.getenv('VEIL_REMOTE_BROWSER'):
        browser_type = 'remote'
    get_executing_test().browser_type = browser_type
    test = get_executing_test()
    test.addCleanup(stop_browser)
    if 'spynner' == browser_type:
        start_spynner_browser(url)
    elif 'chrome' == browser_type:
        start_chrome_browser(url)
    elif 'remote' == browser_type:
        command_executor = 'http://{}:4444/wd/hub'.format(os.getenv('VEIL_REMOTE_BROWSER'))
        start_remote_browser(url, command_executor)
    else:
        raise NotImplementedError('unknown browser type: {}'.format(test.browser_type))


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
            test.error = 'keyboard interrupt'
        check_is_test_failed(test)


def start_chrome_browser(url):
    test = get_executing_test()
    old_cwd = os.getcwd()
    os.chdir('/tmp')
    test.webdriver = selenium.webdriver.Chrome()
    os.chdir(old_cwd)
    test.webdriver.get(url)
    while test.webdriver:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            test.error = 'keyboard interrupt'
        check_is_test_failed(test)


def start_remote_browser(url, command_executor):
    test = get_executing_test()
    capabilities = selenium.webdriver.DesiredCapabilities.INTERNETEXPLORER
    test.webdriver = selenium.webdriver.Remote(command_executor, desired_capabilities=capabilities)
    test.webdriver.get(url)
    while test.webdriver:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            test.error = 'keyboard interrupt'
        check_is_test_failed(test)


def check_is_test_failed(test):
    message = getattr(test, 'error', None)
    if message is not None:
        stop_browser()
        test.fail(message)


def stop_browser():
    test = get_executing_test()
    if 'spynner' == test.browser_type:
        stop_spynner_browser()
    elif test.browser_type in ['chrome', 'remote']:
        stop_webdriver()
    else:
        raise NotImplementedError('unknown browser type: {}'.format(test.browser_type))


def stop_spynner_browser():
    test = get_executing_test()
    browser = test.spynner_browser
    if browser:
        test.spynner_browser = None
        browser.close()


def stop_webdriver():
    test = get_executing_test()
    webdriver = getattr(test, 'webdriver', None)
    if webdriver:
        test.webdriver = None
        webdriver.close()


def inject_page_interaction(html, page_interactions):
    request = get_current_http_request()
    if 'XMLHttpRequest' == request.headers.get('X-Requested-With', None):
        return html
    if not page_interactions:
        return html
    return html.replace('</body>', '{}\n</body>'.format(
        """
        <script type="text/javascript" src="/-test/veil-test.js"></script>
        <script type="text/javascript">$(document).ready(function() {
            %s
        });
        </script>
        """ % page_interactions.pop()
    ))

def load_page_interactions(relative_path):
    module = veil.component.force_import_module(get_executing_test().__module__)
    page_interactions_script = (as_path(os.path.dirname(module.__file__)) / relative_path).text()
    _, _, page_interactions = process_script_elements(page_interactions_script)
    return page_interactions
