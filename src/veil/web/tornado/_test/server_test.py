from __future__ import unicode_literals, print_function, division
import threading
import urllib2
from veil.web.tornado import *
from sandal.fixture import fixtures
from sandal.fixture import UsingFixture

class ServerTest(UsingFixture):
    def test(self):
        def handler():
            get_current_http_response().write('hello')
            get_current_http_response().finish()

        self.http_server=fixtures.start_http_server(handler=handler)
        threading.Thread(target=self.fetch_in_another_thread).start()
        response = fixtures.require_io_loop_executor().execute()
        self.assertEqual('hello', response.data)

    def fetch_in_another_thread(self):
        io_loop_executor = fixtures.require_io_loop_executor()
        with io_loop_executor:
            response = urllib2.urlopen('http://localhost:{}'.format(self.http_server.port))
            response.data = response.read()
            io_loop_executor.stop(response)
