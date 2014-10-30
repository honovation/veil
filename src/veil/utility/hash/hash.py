from __future__ import unicode_literals, print_function, division
import hashlib
import hmac
from logging import getLogger
from veil_installer import *
from veil.environment import *
from veil.server.os import *
from veil.utility.setting import *
from veil.utility.encoding import *
from veil.development.test import get_executing_test

LOGGER = getLogger(__name__)

add_application_sub_resource('hash', lambda config: hash_resource(**config))

_hash_salt = None


@composite_installer
def hash_resource(salt):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'hash.cfg', content='salt={}'.format(salt)))
    return resources


def get_hash_salt():
    global _hash_salt

    if get_executing_test(optional=True):
        return 'secret'
    if _hash_salt is None:
        _hash_salt = load_config_from(VEIL_ETC_DIR / 'hash.cfg', 'salt').salt
    return _hash_salt


def encode_token(*parts):
    signature = get_hmac(*parts, strong=False)
    return '{}|{}'.format('|'.join(unicode(p) for p in parts), signature)


def decode_token(token, *part_types):
    parts = token.split('|')
    if len(parts) != len(part_types) + 1:
        LOGGER.warn('token parts count invalid: %(token)s', {'token': token})
        return None
    if parts[-1] != get_hmac(*parts[:-1], strong=False):
        LOGGER.warn('token signature mismatch: %(token)s', {'token': token})
        return None
    return [t(parts[i]) for i, t in enumerate(part_types)]


def get_password_hash(password, dynamic_salt=None):
    """
    @param dynamic_salt: is recommended for better security,
        it is something like user ID or created_at which is fixed for the secured entity but different from others
    """
    return get_hmac(password, strong=True) if dynamic_salt is None else get_hmac(password, dynamic_salt, strong=True)


def get_hmac(*parts, **kwargs):
    strong = kwargs.get('strong', True)
    digestmod = hashlib.sha256 if strong else hashlib.sha1
    msg = b'|'.join(to_str(p) for p in parts)
    return unicode(hmac.new(to_str(get_hash_salt()), msg, digestmod).hexdigest())


def verify_hmac(hmac_, *parts, **kwargs):
    return hmac_ == get_hmac(*parts, **kwargs)


def get_check_code(*parts, **kwargs):
    size = kwargs.get('size', 6)
    salt = kwargs.get('salt', get_hash_salt())
    msg = b'|'.join(to_str(p) for p in parts)
    return hex(hash(b'{}|{}'.format(to_str(salt), msg)))[-size:].upper()


def verify_check_code(check_code, *parts, **kwargs):
    return check_code == get_check_code(*parts, **kwargs)
