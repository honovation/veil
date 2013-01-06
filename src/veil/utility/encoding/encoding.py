from __future__ import unicode_literals, print_function, division

def to_str(s):
    if isinstance(s, (str, bytes, type(None))):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    raise Exception('to_str does not support {}'.format(type(s)))


def to_unicode(s, encoding=None):
    if isinstance(s, unicode):
        return s
    encoding = encoding or 'utf-8'
    return unicode(s, encoding=encoding)
