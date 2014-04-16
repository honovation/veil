from __future__ import unicode_literals, print_function, division
import urllib2
from veil.development.test import TestCase
from .executor import require_io_loop_executor
from .server import start_test_http_server
from .context import get_current_http_response

class ServerTest(TestCase):
    def test(self):
        def handler():
            get_current_http_response().write('hello')
            get_current_http_response().finish()

        self.http_server = start_test_http_server(handler=handler, port=18080)
        with require_io_loop_executor():
            response = urllib2.urlopen('http://localhost:{}'.format(self.http_server.port))
            response.data = response.read()
            self.assertEqual('hello', response.data)