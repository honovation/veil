from __future__ import unicode_literals, print_function, division
import logging
import functools
from veil.utility.encoding import *


def traced(level='INFO', color=None):
    level = getattr(logging, level)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_message = ', '.join(to_unicode(arg, strict=False) for arg in args)
            if kwargs:
                args_message = '{}, {}'.format(args_message, ', '.join('{}=%({})s'.format(k, k) for k in kwargs))
            log_message = 'executing {}.{}({})...'.format(func.__module__, func.__name__, args_message)
            logging.getLogger(func.__module__).log(level, log_message, dict(kwargs, args=args, __color__=color))
            return func(*args, **kwargs)

        return wrapper

    return decorator