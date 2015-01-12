# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from cache import LruCache


def memoize(maxsize=None, timeout=None):
    if hasattr(maxsize, '__call__'):
        func = maxsize
        decorator = LruCache()
        return decorator(func)
    return LruCache(maxsize, timeout)
