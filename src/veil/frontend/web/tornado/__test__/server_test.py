from __future__ import unicode_literals, print_function, division
import threading
import urllib2
from sandal.test import TestCase
from ..executor import require_io_loop_executor
from ..server import start_test_http_server
from ..context import get_current_http_response

class ServerTest(TestCase):
    def test(self):
        def handler():
            get_current_http_response().write('hello')
            get_current_http_response().finish()

        self.http_server = start_test_http_server(handler=handler)
        threading.Thread(target=self.fetch_in_another_thread).start()
        response = require_io_loop_executor().execute()
        self.assertEqual('hello', response.data)

    def fetch_in_another_thread(self):
        io_loop_executor = require_io_loop_executor()
        with io_loop_executor:
            response = urllib2.urlopen('http://localhost:{}'.format(self.http_server.port))
            response.data = response.read()
            io_loop_executor.stop(response)
