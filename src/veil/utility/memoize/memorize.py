# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from cache import LruCache


def memorize(maxsize=None, timeout=None):
    if hasattr(maxsize, '__call__'):
        func = maxsize
        decorator = _LruCache()
        return decorator(func)
    return _LruCache(maxsize, timeout)


class _LruCache(LruCache):
    def invalidate(self):
        self.cache.clear()
