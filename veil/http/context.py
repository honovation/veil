from __future__ import print_function, division
import contextlib

http_contexts = []


def get_current_http_context():
    if not http_contexts:
        raise Exception('not inside http context')
    return http_contexts[-1]


def get_current_http_request():
    return get_current_http_context().request


def get_current_http_response():
    return get_current_http_context().response


@contextlib.contextmanager
def require_current_http_context_being(http_context):
    http_contexts.append(http_context)
    try:
        yield
    finally:
        http_contexts.pop()


class HTTPContext(object):
    def __init__(self, request, response):
        self.request = request
        self.response = response