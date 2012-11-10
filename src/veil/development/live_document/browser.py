from __future__ import unicode_literals, print_function, division
import contextlib
import threading
import traceback
import os
import atexit
import selenium.webdriver
import selenium.common.exceptions
import jinjatag
from veil.environment import *
from veil.frontend.web import *
from veil.development.test import *
from .live_document import require_current_context_being

website_threads = {}
webdriver = None

@contextlib.contextmanager
def open_browser_page(website, path, page_name):
    require_website_running(website)
    webdriver = require_webdriver()
    webdriver.get(get_url(website, path))
    current_page = webdriver.execute_script('return veil.doc.currentPage;')
    if page_name != current_page['pageName']:
        raise Exception('we are on the wrong page, expected: {}, actual: {}'.format(
            page_name, current_page['pageName']))
    with require_current_context_being(BrowserPageContext()):
        yield


class BrowserPageContext(object):
    def __call__(self, statement_name, args):
        try:
            return require_webdriver().execute_script(
                "return veil.doc.currentPage['{}'].apply(this, arguments);".format(statement_name), *args)
        except selenium.common.exceptions.WebDriverException, e:
            if 'modal dialog' in e.msg:
                require_webdriver().switch_to_alert().accept()
            else:
                raise


def require_webdriver():
    global webdriver
    if webdriver:
        return webdriver
    old_cwd = os.getcwd()
    os.chdir('/tmp')
    try:
        webdriver = selenium.webdriver.Chrome()
        atexit.register(webdriver.close)
        return webdriver
    finally:
        os.chdir(old_cwd)


def require_website_running(website):
    if website in website_threads:
        return
    start_test_website(website)
    website_threads[website] = threading.Thread(target=lambda: execute_io_loop(60))
    website_threads[website].daemon = True
    website_threads[website].start()


def execute_io_loop(timeout):
    get_executing_test().addCleanup(require_io_loop_executor().stop)
    try:
        require_io_loop_executor().execute(timeout=timeout)
    except:
        traceback.print_exc()
        raise


def get_url(website, path):
    domain = get_website_option(website, 'domain')
    domain_port = get_website_option(website, 'domain_port')
    url_prefix = 'http://{}:{}'.format(domain, domain_port)
    return '{}{}'.format(url_prefix, path)


@jinjatag.simple_block()
def doc(body):
    if 'test' == VEIL_SERVER:
        return '<script type="text/javascript" src="{}"></script>\n{}'.format(static_url('veil-doc.js'), body)
    else:
        return ''