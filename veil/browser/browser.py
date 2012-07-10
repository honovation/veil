from __future__ import unicode_literals, print_function, division
import html5lib
from cookielib import CookieJar
import httplib
from threading import Thread, Lock
import urllib
import urllib2
import urlparse
from logging import getLogger
from pyquery import PyQuery
from sandal.encoding import to_str, to_unicode
from sandal.fixture import fixture, fixtures
from sandal.fixture import get_executing_test
from .action import ActionMixin
from .form import FormMixin
from .query import QueryMixin
from .select import SelectMixin

LOGGER = getLogger(__name__)

@fixture
def start_browser(default_netloc=None, http_server=None, browser_type='ie6'):
    assert default_netloc or http_server
    default_netloc = default_netloc or 'localhost:{}'.format(http_server.port)
    return Browser(default_netloc, browser_type)


@fixture
def start_website_and_browser(website, **kwargs):
    http_server = fixtures.start_website(website, **kwargs)
    return start_browser(http_server=http_server)


class Browser(QueryMixin, ActionMixin, FormMixin, SelectMixin):
    def __init__(self, default_netloc, browser_type):
        self.default_netloc = default_netloc
        self.cookie_jar = CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar), SilentHTTPErrorProcessor())
        self.pages = []
        self.browser_type = browser_type
        self.fetching = Lock()

    @property
    def cookies(self):
        return dict((cookie.name, cookie) for cookie in self.cookie_jar)

    @property
    def page(self):
        if not self.pages:
            raise Exception('not inside a page')
        return self.pages[-1]

    def fetch(self, *url_segments, **kwargs):
        method = kwargs.get('method', 'GET').upper()
        kwargs.pop('method', None)
        if 'GET' == method:
            return self.get(*url_segments, **kwargs)
        elif 'POST' == method:
            return self.post(*url_segments, **kwargs)
        elif 'PUT' == method:
            return self.put(*url_segments, **kwargs)
        elif 'DELETE' == method:
            return self.delete(*url_segments, **kwargs)
        raise Exception('unsupported method: {}'.format(method))

    def get(self, *url_segments, **kwargs):
        return self._fetch(*url_segments, **kwargs)

    def post(self, *url_segments, **kwargs):
        arguments = kwargs.get('arguments', {})
        kwargs.pop('arguments', None)
        data = kwargs.get('data', None)
        if arguments:
            if data:
                kwargs['data'] = '{}&{}'.format(urlencode(arguments), data)
            else:
                kwargs['data'] = urlencode(arguments)

        else:
            kwargs['data'] = data or ''
        if kwargs.pop('auto_xsrf', True):
            kwargs.setdefault('headers', {})['X-XSRF'] = get_xsrf_token(self)
        return self._fetch(*url_segments, **kwargs)

    def put(self, *url_segments, **kwargs):
        arguments = dict(kwargs.get('arguments', {}))
        arguments['_method'] = 'PUT'
        kwargs['arguments'] = arguments
        return self.post(*url_segments, **kwargs)

    def delete(self, *url_segments, **kwargs):
        arguments = dict(kwargs.get('arguments', {}))
        arguments['_method'] = 'DELETE'
        kwargs['arguments'] = arguments
        return self.post(*url_segments, **kwargs)

    def _fetch(self, *url_segments, **kwargs):
        expected_status_code = kwargs.pop('expected_status_code', httplib.OK)
        arguments = kwargs.pop('arguments', {})

        url = ''.join([str(url_segment) for url_segment in url_segments])
        schema, netloc, path, params, query, fragment = urlparse.urlparse(url)
        schema = schema or 'http'
        netloc = netloc or self.default_netloc
        assert len(path) > 0
        params = ''
        arguments.update(urlparse.parse_qs(query))
        query = urlencode(arguments)
        fragment = ''
        url = urlparse.urlunparse((schema, netloc, path, params, query, fragment))
        request = create_request(url=url, **kwargs)
        self.fetching.acquire()
        Thread(target=self.fetch_in_another_thread, args=(request,)).start()
        try:
            page = fixtures.require_io_loop_executor().execute()
        except:
            LOGGER.error('failed to fetch {}'.format(url))
            raise
        page.assert_status_code(expected_status_code)
        return page

    def fetch_in_another_thread(self, request):
        try:
            io_loop_executor = fixtures.require_io_loop_executor()
            with io_loop_executor:
                response = self.opener.open(request, timeout=5)
                response.data = response.read()
                page = BrowserPage(self, request, response=response)
                io_loop_executor.stop(page)
        except:
            LOGGER.exception('failed to fetch {}'.format(request.get_full_url()))
        self.fetching.release()


def create_request(url, **kwargs):
    url = to_str(url)
    if kwargs.get('headers', None) is not None:
        kwargs['headers'] = dict((to_str(key), to_str(value)) for key, value in kwargs['headers'].items())
    if kwargs.get('data', None) is not None:
        kwargs['data'] = to_str(kwargs['data'])
    return urllib2.Request(url=url, **kwargs)


def urlencode(arguments):
    normalized_arguments = []
    for key, values in arguments.items():
        values = values if isinstance(values, list) or isinstance(values, tuple) else [values]
        for value in values:
            normalized_arguments.append((to_str(key), to_str(value)))
    return urllib.urlencode(normalized_arguments)


def get_xsrf_token(browser):
    if '_xsrf' not in browser.cookies:
        browser.get('/_xsrf', expected_status_code=httplib.NOT_FOUND)
    if '_xsrf' not in browser.cookies:
        raise Exception('_xsrf cookie not found')
    return browser.cookies['_xsrf'].value


class BrowserPage(object):
    def __init__(self, browser, request, response=None):
        self.browser = browser
        self.request = request
        self.response = response

    @property
    def response_text(self):
        return to_unicode(self.response.data)

    @property
    def dom(self):
        if not hasattr(self, '_dom'):
            if not self.response.data:
                raise Exception('response_data is empty')
            try:
                parser = html5lib.HTMLParser(
                    tree=html5lib.treebuilders.getTreeBuilder("lxml"), namespaceHTMLElements=False)
                tree = parser.parse(self.response.data)
                self._dom = PyQuery(tree.getroot())
            except:
                LOGGER.exception('failed to build dom from {}'.format(self.response.data))
                raise
        return self._dom

    @property
    def status_code(self):
        return self.response.code

    def assert_status_code(self, expected_status_code):
        if self.status_code == expected_status_code:
            return
        get_executing_test().fail(
            """
            response code is not {expected_status_code}, but {actual_status_code}
            request url: {request_url}
            request data: {request_data}
            response data: {response_data}
            """.format(
                expected_status_code=expected_status_code,
                actual_status_code=self.status_code,
                request_url=self.request.get_full_url(),
                request_data=to_unicode(self.request.data) if self.request.data else None,
                response_data=self.response_text))

    def __enter__(self):
        self.browser.pages.append(self)

    def __exit__(self, type, value, traceback):
        self.browser.pages.pop()


class SilentHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    handler_order = 1000  # after all other processing

    def http_response(self, request, response):
        return response

    https_response = http_response