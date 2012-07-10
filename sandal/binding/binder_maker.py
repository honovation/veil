"""
binder maker takes binder as input and makes binder as result
"""
from __future__ import unicode_literals, print_function, division

def compose(*binders):
    """
    Applies each of a series of validators in turn, passing the return
    value of each to the next.
    """
    return CompositeBinder(binders)


class CompositeBinder(object):
    def __init__(self, binders):
        self.binders = binders

    def __call__(self, value):
        for binder in self.binders:
            bind = binder
            value = bind(value)
        return value


def each(*binders):
    def bind(value):
        composite_binder = CompositeBinder(binders)
        return [composite_binder(item) for item in value]

    return bind

def optional(*binders, **kwargs):
    def bind(value):
        composite_binder = CompositeBinder(binders)

        if value is None:
            return kwargs.get('default')
        return composite_binder(value)

    return bind
