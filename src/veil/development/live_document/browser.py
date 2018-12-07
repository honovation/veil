# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import contextlib
import os
import jinjatag
import atexit
import time
from veil_component import VEIL_ENV
from veil.frontend.web import *
from veil.development.test import *
from .live_document import require_current_context_being
from .live_document import document_statement

LOGGER = logging.getLogger(__name__)
current_http_server = None
webdriver = None

if not VEIL_ENV.is_test:
    def open_browser_page(website_purpose, path, page_name):
        pass

    def report_error(message):
        pass
else:
    import selenium.webdriver
    import selenium.common.exceptions

    @contextlib.contextmanager
    def open_browser_page(website_purpose, path, page_name):
        ensure_website_running(website_purpose)
        with require_current_context_being(BrowserPageContext(page_name)):
            with require_io_loop_executor():
                webdriver = require_webdriver()
                webdriver.get(get_url(website_purpose, path))
                assert_current_page(page_name)
                yield

    def ensure_website_running(purpose):
        get_executing_test().addCleanup(reset_current_http_server)
        global current_http_server
        if current_http_server:
            if current_http_server.purpose == purpose:
                pass
            else:
                current_http_server.stop()
                current_http_server = start_test_website(purpose)
        else:
            current_http_server = start_test_website(purpose)

    def reset_current_http_server():
        global current_http_server
        current_http_server.stop()
        current_http_server = None

    @document_statement('确认所在页面')
    @contextlib.contextmanager
    def enter_browser_page_context(page_name):
        assert_current_page(page_name)
        with require_current_context_being(BrowserPageContext(page_name)):
            with require_io_loop_executor():
                yield

    class BrowserPageContext(object):
        def __init__(self, page_name):
            super(BrowserPageContext, self).__init__()
            self.page_name = page_name

        def __call__(self, statement_name, args):
            try:
                assert_current_page(self.page_name)
                return_value = require_webdriver().execute_script('''
                    if (!veil.doc.currentPage['{}']) {{
                        return 'NO_STATEMENT';
                    }}
                    return veil.doc.currentPage['{}'].apply(this, arguments);
                    '''.format(statement_name, statement_name), *filter_non_serializable(args))
                if 'NO_STATEMENT' == return_value:
                    report_error('statement {} not defined'.format(statement_name))
                else:
                    return return_value
            except selenium.common.exceptions.WebDriverException as e:
                if 'modal dialog' in e.msg:
                    require_webdriver().switch_to.alert().accept()
                else:
                    assert_no_js_errors()
                    raise
            except Exception:
                assert_no_js_errors()
                raise

    def assert_current_page(page_name):
        current_page_name = require_webdriver().execute_script('''
            if (window.veil && veil.doc && veil.doc.currentPage) {
                return veil.doc.currentPage.pageName;
            } else {
                return null;
            }
            ''')
        if page_name != current_page_name:
            assert_no_js_errors()
            message = 'we are on the wrong page, expected: {}, actual: {}, url: {}'.format(
                page_name, current_page_name, webdriver.current_url)
            report_error(message)

    def assert_no_js_errors():
        js_errors = require_webdriver().execute_script('''
            if (window.veil && veil.doc) {
                return veil.doc.jsErrors
            } else {
                return null;
            }
            ''')
        if js_errors:
            report_error('java script errors: {}'.format(js_errors))

    def report_error(message):
        LOGGER.error(message)
        import time
        time.sleep(60)
        raise Exception(message)

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
            options = selenium.webdriver.ChromeOptions()
            options.add_argument('incognito')
            options.add_argument('auto-open-devtools-for-tabs')
            chromium_binary_location = '/usr/bin/chromium-browser'
            if os.path.exists(chromium_binary_location):
                options.binary_location = chromium_binary_location
            webdriver = selenium.webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)
            atexit.register(webdriver.close)  # only close when we finished everything
            get_executing_test().addCleanup(webdriver.delete_all_cookies)  # delete all cookies to isolate document-checking
            return webdriver
        finally:
            os.chdir(old_cwd)

    def get_url(purpose, path):
        website_url = get_website_url(purpose)
        return '{}{}'.format(website_url, path)


@jinjatag.simple_block()
def doc(body):
    if VEIL_ENV.is_test:
        return '<script type="text/javascript" src="{}"></script>\n{}'.format(static_url('veil-doc.js'), body)
    else:
        return ''
