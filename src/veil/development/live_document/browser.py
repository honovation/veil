# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
import threading
import traceback
import os
import selenium.webdriver
import selenium.common.exceptions
import jinjatag
import atexit
import tornado.ioloop
from veil.environment import *
from veil.frontend.web import *
from veil.development.test import *
from veil.frontend.website_setting import get_website_options
from .live_document import require_current_context_being
from .live_document import document_statement

website_threads = {}
webdriver = None

def open_browser_page(website, path, page_name):
    require_website_running(website)
    webdriver = require_webdriver()
    webdriver.get(get_url(website, path))
    return assert_current_page(page_name)

@document_statement('确认所在页面')
@contextlib.contextmanager
def assert_current_page(page_name):
    current_page_name = webdriver.execute_script(
        """
        if (window.veil && veil.doc && veil.doc.currentPage) {
            return veil.doc.currentPage.pageName;
        } else {
            return null;
        }
        """)
    if page_name != current_page_name:
        message = 'we are on the wrong page, expected: {}, actual: {}, url: {}'.format(
            page_name, current_page_name, webdriver.current_url)
        print(message)
        import time
        time.sleep(60)
        raise Exception(message)
    with require_current_context_being(BrowserPageContext()):
        yield

class BrowserPageContext(object):
    def __call__(self, statement_name, args):
        try:
            return require_webdriver().execute_script(
                "return veil.doc.currentPage['{}'].apply(this, arguments);".format(statement_name),
                *filter_non_serializable(args))
        except selenium.common.exceptions.WebDriverException, e:
            if 'modal dialog' in e.msg:
                require_webdriver().switch_to_alert().accept()
            else:
                assert_no_js_errors()
                raise
        except:
            assert_no_js_errors()
            raise

def assert_no_js_errors():
    js_errors = require_webdriver().execute_script(
        """
        if (window.veil && veil.doc) {
            return veil.doc.jsErrors
        } else {
            return null;
        }
        """)
    if js_errors:
        raise Exception('java script errors: {}'.format(js_errors))


def filter_non_serializable(arg):
    SERIZABLE_TYPES = (basestring, int, float, dict, tuple, list)
    if isinstance(arg, dict):
        return {k: filter_non_serializable(v) for k, v in arg.items() if isinstance(v, SERIZABLE_TYPES)}
    elif isinstance(arg, (tuple, list)):
        return [filter_non_serializable(e) for e in arg if isinstance(e, SERIZABLE_TYPES)]
    else:
        if isinstance(arg, SERIZABLE_TYPES):
            return arg
        else:
            raise Exception('can not serialze: {}'.format(arg))


def require_webdriver():
    global webdriver
    if webdriver:
        return webdriver
    old_cwd = os.getcwd()
    os.chdir('/tmp')
    try:
        webdriver = selenium.webdriver.Chrome()
        atexit.register(webdriver.close) # only close when we finished everything
        get_executing_test().addCleanup(webdriver.delete_all_cookies) # delete all cookies to isolate document-checking
        return webdriver
    finally:
        os.chdir(old_cwd)


def require_website_running(website):
    get_executing_test().addCleanup(website_threads.clear)
    if website in website_threads:
        return
    if website_threads:
        raise Exception('do not support running two websites at the same time')
    start_test_website(website)
    website_threads[website] = threading.Thread(target=lambda: execute_io_loop(60))
    website_threads[website].daemon = True
    website_threads[website].start()


def execute_io_loop(timeout):
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        traceback.print_exc()
        raise


def get_url(website, path):
    website_options = get_website_options(website)
    domain = website_options.domain
    domain_port = website_options.domain_port
    url_prefix = 'http://{}:{}'.format(domain, domain_port)
    return '{}{}'.format(url_prefix, path)


@jinjatag.simple_block()
def doc(body):
    if 'test' == VEIL_SERVER:
        return '<script type="text/javascript" src="{}"></script>\n{}'.format(static_url('veil-doc.js'), body)
    else:
        return ''