# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import functools
import inspect
import weakref
import time


def memoize(max_size=None, max_age=None):
    if hasattr(max_size, '__call__'):
        func = max_size
        decorator = _memoize()
        return decorator(func)
    return _memoize(max_size, max_age)


def _memoize(max_size=None, max_age=None):
    class Memoizer(object):
        """
        Decorator. Caches a function's return value each time it is called.
        If called later with the same arguments, the cached value is returned
        (not reevaluated).
        """

        caches = weakref.WeakSet()

        def __init__(self, func):
            self.func = func
            self.max_size = max_size
            self.max_age = max_age
            self.cache = {}
            self.size = 0
            Memoizer.caches.add(self)

        def __call__(self, *args, **kwargs):
            key = self.key(args, kwargs)
            try:
                if self.max_age:
                    now = time.time()
                    value, cached_at = self.cache[key]
                    age = now - cached_at
                    if age > self.max_age:
                        raise KeyError('expired')
                else:
                    value = self.cache[key]
                return value
            except KeyError:
                value = self.func(*args, **kwargs)
                if self.max_size is None or self.size < self.max_size:
                    if self.max_age:
                        self.cache[key] = (value, now)
                    else:
                        self.cache[key] = value
                    self.size += 1
                return value
            except TypeError:
                # uncachable -- for instance, passing a list as an argument.
                # Better to not cache than to blow up entirely.
                return self.func(*args, **kwargs)

        def __repr__(self):
            """Return the function's docstring."""
            return self.func.__doc__

        def __get__(self, obj, objtype):
            """Support instance methods."""
            fn = functools.partial(self.__call__, obj)
            fn.reset = self.reset_
            return fn

        def reset_(self):
            self.cache = {}
            self.size = 0

        def normalize_args(self, args, kwargs):
            spec = inspect.getargs(self.func.__code__).args
            return dict(kwargs.items() + zip(spec, args))

        def key(self, args, kwargs):
            a = self.normalize_args(args, kwargs)
            return tuple(sorted(a.items()))

        @staticmethod
        def reset():
            for memo in Memoizer.caches:
                memo.reset_()

    return Memoizer
