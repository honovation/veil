from __future__ import unicode_literals, print_function, division
import hashlib
import hmac
from logging import getLogger
from sandal.option import register_option

LOGGER = getLogger(__name__)

get_hash_salt = register_option('security', 'hash_salt')

def encode_token(*parts):
    parts = [unicode(p) for p in parts]
    parts.append(get_hmac(*parts, strong=False))
    return '|'.join(parts)


def decode_token(token, *part_types):
    parts = token.split('|')
    if len(parts) != len(part_types) + 1:
        LOGGER.warn('token parts count invalid: {}'.format(token))
        return None
    if parts[-1] != get_hmac(*parts[:-1], strong=False):
        LOGGER.warn('token signature mismatch: {}'.format(token))
        return None
    return [t(parts[i]) for i, t in enumerate(part_types)]


def get_password_hash(password):
    return get_hmac(password, strong=True)


def get_hmac(*parts, **kwargs):
    strong = kwargs.get('strong', True)
    salt = kwargs.get('salt', get_hash_salt())
    digestmod = hashlib.sha256 if strong else hashlib.sha1
    msg = '|'.join([str(part) for part in parts])
    return hmac.new(str(salt), msg, digestmod).hexdigest()


def verify_hmac(hmac, *parts, **kwargs):
    return hmac == get_hmac(*parts, **kwargs)


def get_check_code(*parts, **kwargs):
    size = kwargs.get('size', 6)
    salt = kwargs.get('salt', get_hash_salt())
    msg = '|'.join([str(part) for part in parts])
    return hex(hash(str(salt) + msg))[-size:]


def verify_check_code(check_code, *parts, **kwargs):
    return check_code == get_check_code(*parts, **kwargs)
