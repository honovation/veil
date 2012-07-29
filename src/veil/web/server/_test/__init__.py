from __future__ import unicode_literals, print_function, division
from sandal.fixture import fixture, fixtures
from ..website import create_website_http_handler

@fixture
def start_website(website, **kwargs):
    http_handler = create_website_http_handler(website, **kwargs)
    return fixtures.start_http_server(handler=http_handler)