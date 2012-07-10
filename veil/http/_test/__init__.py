from __future__ import unicode_literals, print_function, division
from sandal.fixture import fixture
from sandal.fixture import get_executing_test
from ..server import create_http_server
from sandal.template import reset_template_environment

@fixture
def start_http_server(port=10000, **kwargs):
    test = get_executing_test()
    if hasattr(test, '_http_server'):
        raise Exception('can only start one server for a test')
    test.addCleanup(reset_template_environment)
    test._http_server = create_http_server(**kwargs)
    test._http_server.listen(port)
    test._http_server.port = port
    test.addCleanup(test._http_server.stop)
    return test._http_server

@fixture
def require_http_server():
    test = get_executing_test()
    if not hasattr(test, '_http_server'):
        raise Exception('http server not started yet')
    return test._http_server
