from __future__ import unicode_literals, print_function, division
import hashlib
import hmac
from logging import getLogger
from veil.development.test import get_executing_test

LOGGER = getLogger(__name__)

DEFAULT_SECURE_HASH_SALT = '953236d83dd3401c9228f77ec2140b9d'
secure_hash_salt = DEFAULT_SECURE_HASH_SALT

def set_secure_hash_salt(value):
    global secure_hash_salt
    secure_hash_salt = value


def encode_token(*parts):
    parts = [unicode(p) for p in parts]
    parts.append(get_hmac(*parts, strong=False))
    return '|'.join(parts)


def decode_token(token, *part_types):
    parts = token.split('|')
    if len(parts) != len(part_types) + 1:
        LOGGER.warn('token parts count invalid: %(token)s', {'token': token})
        return None
    if parts[-1] != get_hmac(*parts[:-1], strong=False):
        LOGGER.warn('token signature mismatch: %(token)s', {'token': token})
        return None
    return [t(parts[i]) for i, t in enumerate(part_types)]


def get_password_hash(password):
    return get_hmac(password, strong=True)


def get_hmac(*parts, **kwargs):
    strong = kwargs.pop('strong', True)

    salt = kwargs.pop('salt', secure_hash_salt)
    executing_test = get_executing_test(optional=True)
    if executing_test:
        salt = DEFAULT_SECURE_HASH_SALT

    digestmod = hashlib.sha256 if strong else hashlib.sha1
    msg = '|'.join([str(part) for part in parts])
    return hmac.new(str(salt), msg, digestmod).hexdigest()


def verify_hmac(hmac, *parts, **kwargs):
    return hmac == get_hmac(*parts, **kwargs)


def get_check_code(*parts, **kwargs):
    size = kwargs.pop('size', 6)
    salt = kwargs.pop('salt')
    msg = '|'.join([str(part) for part in parts])
    return hex(hash(str(salt) + msg))[-size:]


def verify_check_code(check_code, *parts, **kwargs):
    return check_code == get_check_code(*parts, **kwargs)


def calculate_file_md5_hash(file_object, reset_position=False, hex=True):
    """ Calculate the md5 hash for this file.

    This reads through the entire file.
    """
    assert file_object is not None and file_object.tell() == 0
    try:
        m = hashlib.md5()
        for chunk in iter_file_in_chunks(file_object):
            m.update(chunk)
        return m.hexdigest() if hex else m.digest()
    finally:
        if reset_position:
            file_object.seek(0)


def iter_file_in_chunks(file_object, chunk_size=8192):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k."""
    return iter(lambda : file_object.read(chunk_size), b'')