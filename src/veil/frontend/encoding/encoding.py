from __future__ import unicode_literals, print_function, division
from chardet import universaldetector
from veil.model.collection import DictObject


def to_str(s):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(s, (str, bytes, type(None))):
        return s
    if isinstance(s, unicode):
        return s.encode("utf-8")
    raise Exception('to_str does not support {}'.format(type(s)))


def to_unicode(s, encoding=None, detects_encoding=False):
    """transform s to its unicode representation

    When detects_encoding is False, it will do the transformation with the specified encoding or
        'utf-8' if not specified;
    When detects_encoding is True, it will always check if there is a better encoding than the specified one.
        If there is a better one, it will use the one for the transformation,
        otherwise use the specified one or 'utf-8' if not specified.
    """
    if isinstance(s, unicode):
        return s
    encoding = encoding or 'utf-8'
    if detects_encoding:
        detected_encoding = detect_encoding(s, encoding).encoding
        encoding = detected_encoding or encoding
    return unicode(s, encoding=encoding)


detector = universaldetector.UniversalDetector()


def detect_encoding(s, encoding=None):
    assert type(s) is not unicode

    if encoding is not None:
        try:
            unicode(s, encoding=encoding)
        except UnicodeDecodeError:
            pass
        else:
            return DictObject(encoding=encoding, confidence=1)
    if encoding is None or encoding.lower() not in {'utf-8', 'utf8', 'u8', 'utf'}:
        try:
            unicode(s, encoding='utf-8')
        except UnicodeDecodeError:
            pass
        else:
            return DictObject(encoding='utf-8', confidence=1)
    if encoding is None or encoding.lower() != 'gb18030':
        try:
            unicode(s, encoding='gb18030')
        except UnicodeDecodeError:
            pass
        else:
            return DictObject(encoding='gb18030', confidence=1)

    detector.reset()
    detector.feed(s)
    detector.close()
    return DictObject(detector.result)


def detect_file_encoding(file_object, encoding=None):
    assert file_object is not None and file_object.tell() == 0

    is_encoding = encoding is not None
    is_utf_8 = encoding is None or encoding.lower() not in {'utf-8', 'utf8', 'u8', 'utf'}
    is_gb18030 = encoding is None or encoding.lower() != 'gb18030'

    detector.reset()
    try:
        for line in file_object:
            if is_encoding:
                try:
                    unicode(line, encoding=encoding)
                except UnicodeDecodeError:
                    is_encoding = False
            if is_utf_8:
                try:
                    unicode(line, encoding='utf-8')
                except UnicodeDecodeError:
                    is_utf_8 = False
            if is_gb18030:
                try:
                    unicode(line, encoding='gb18030')
                except UnicodeDecodeError:
                    is_gb18030 = False
            detector.feed(line)
            if not is_encoding and not is_utf_8 and not is_gb18030 and detector.done:
                break
    finally:
        file_object.seek(0)
    detector.close()

    if is_encoding:
        return DictObject(encoding=encoding, confidence=1)
    if is_utf_8:
        return DictObject(encoding='utf-8', confidence=1)
    if is_gb18030:
        return DictObject(encoding='gb18030', confidence=1)
    return DictObject(detector.result)
