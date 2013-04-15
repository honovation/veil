from __future__ import unicode_literals, print_function, division
import logging

LOGGER = logging.getLogger(__name__)

def to_str(s):
    if isinstance(s, (str, bytes)):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)


def to_unicode(s, encoding=None):
    if isinstance(s, unicode):
        return s
    if isinstance(s, (str, bytes)):
        encoding = encoding or 'utf-8'
        return unicode(s, encoding=encoding)
    return unicode(s)
