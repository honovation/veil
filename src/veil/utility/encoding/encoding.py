from __future__ import unicode_literals, print_function, division
import logging

LOGGER = logging.getLogger(__name__)

def to_str(s):
    if isinstance(s, (str, bytes)):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)


def to_unicode(s, encoding='utf-8', remedial_encodings=('gb18030',), strict=True, additional=None):
    if isinstance(s, unicode):
        return s

    if isinstance(s, (str, bytes)):
        if encoding in remedial_encodings:
            encodings = remedial_encodings
        else:
            encodings = (encoding, ) + remedial_encodings
        for e in encodings:
            try:
                return unicode(s, encoding=e)
            except UnicodeDecodeError:
                if e == encodings[-1]:
                    u = unicode(repr(s)[1:-1])
                    LOGGER.warning('to_unicode failed: %(tried_encodings)s, %(u)s, %(additional)s', {
                        'tried_encodings': encodings,
                        'u': u,
                        'additional': additional
                    })
                    if strict:
                        raise
                    else:
                        return u

    try:
        return unicode(s)
    except UnicodeDecodeError:
        u = unicode(repr(s))
        LOGGER.warning('to_unicode failed: %(u)s, %(additional)s', {'u': u, 'additional': additional})
        if strict:
            raise
        else:
            return u
