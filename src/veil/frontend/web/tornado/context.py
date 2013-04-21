from __future__ import print_function, division
import contextlib

http_contexts = []


def get_current_http_context(optional=False):
    if not http_contexts:
        if optional:
            return None
        else:
            raise Exception('not inside http context')
    return http_contexts[-1]


def get_current_http_request(optional=False):
    context = get_current_http_context(optional=optional)
    return context.request if context else None


def get_current_http_response(optional=False):
    context =get_current_http_context(optional=optional)
    return context.response if context else None


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