from __future__ import unicode_literals, print_function, division
import functools

executing_handlers = []

def decorate_handler(handler):
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        executing_handlers.append(handler)
        try:
            return handler(*args, **kwargs)
        finally:
            executing_handlers.pop()

    return wrapper


def get_executing_handler():
    if executing_handlers:
        return executing_handlers[-1]
    else:
        return None