from __future__ import unicode_literals, print_function, division


def verify(value):
    if not value:
        raise Exception('verification failed')