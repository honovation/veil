from __future__ import unicode_literals, print_function, division
import base64
import calendar
import datetime
import email.utils
from logging import getLogger
import re
import time
from veil.utility.encoding import *
from veil.utility.hash import *
from .context import get_current_http_request
from .context import get_current_http_response

LOGGER = getLogger(__name__)

def get_secure_cookie(name, value=None, default=None, max_age_days=31, request=None):
    if value is None:
        value = get_cookie(name, request=request)
    if not value:
        return default
    parts = value.split('|')
    if len(parts) != 3:
        return default
    signature = get_hmac(name, parts[0], parts[1], strong=False)
    if not _time_independent_equals(parts[2], signature):
        LOGGER.warning('Invalid cookie signature: %(name)s, %(value)s', {'name': name, 'value': value})
        return default
    timestamp = int(parts[1])
    if timestamp < time.time() - max_age_days * 86400:
        LOGGER.warning('Expired cookie: %(name)s, %(value)s', {'name': name, 'value': value})
        return default
    if timestamp > time.time() + 31 * 86400:
        # _cookie_signature does not hash a delimiter between the
        # parts of the cookie, so an attacker could transfer trailing
        # digits from the payload to the timestamp without altering the
        # signature.  For backwards compatibility, sanity-check timestamp
        # here instead of modifying _cookie_signature.
        LOGGER.warning('Cookie timestamp in future; possible tampering %(name)s, %(value)s', {'name': name, 'value': value})
        return default
    if parts[1].startswith('0'):
        LOGGER.warning('Tampered cookie: %(name)s, %(value)s', {'name': name, 'value': value})
        return default
    try:
        return to_unicode(base64.b64decode(parts[0]))
    except:
        return default


def set_secure_cookie(response=None, name=None, value=None, expires_days=30, **kwargs):
    response = response or get_current_http_response()
    create_secure_cookie(response.cookies, name, value, expires_days, **kwargs)


def create_secure_cookie(cookies, name, value, expires_days, **kwargs):
    timestamp = str(int(time.time()))
    value = base64.b64encode(to_str(value))
    signature = get_hmac(name, value, timestamp, strong=False)
    value = '|'.join((value, timestamp, signature))
    return create_cookie(cookies, name=name, value=value, expires_days=expires_days, **kwargs)


def get_cookies(request=None):
    request = request or get_current_http_request(optional=True)
    return request.cookies if request else {}


def get_cookie(name, default=None, request=None):
    cookie_from_response = get_cookie_from_response(name)
    if cookie_from_response:
        return cookie_from_response
    cookies = get_cookies(request=request)
    if name in cookies:
        try:
            return to_unicode(cookies[name].value)
        except:
            return default
    return default


def get_cookie_from_response(name):
    current_http_response = get_current_http_response(optional=True)
    if current_http_response and name in current_http_response.cookies:
        try:
            return to_unicode(current_http_response.cookies[name].value)
        except:
            return None
    return None


def clear_cookies(request=None, response=None):
    for name in get_cookies(request=request):
        clear_cookie(name, response=response)


def clear_cookie(name, path='/', domain=None, response=None):
    expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    set_cookie(response=response, name=name, value='', path=path, expires=expires, domain=domain)


def set_cookie(response=None, **kwargs):
    response = response or get_current_http_response()
    create_cookie(response.cookies, **kwargs)


def create_cookie(cookies, name, value, domain=None, expires=None, path='/', expires_days=None, expires_minutes=None, **kwargs):
    name = to_str(name)
    value = to_str(value)
    if re.search(br'[\x00-\x20]', name + value):
        # Don't let us accidentally inject bad stuff
        raise ValueError('Invalid cookie {}: {}'.format(name, value))
    cookies[name] = value
    cookie = cookies[name]
    if domain:
        cookie['domain'] = domain
    if not expires and (expires_days is not None or expires_minutes is not None):
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days or 0, minutes=expires_minutes or 0)
    if expires:
        timestamp = calendar.timegm(expires.utctimetuple())
        cookie['expires'] = email.utils.formatdate(timestamp, localtime=False, usegmt=True)
    if path:
        cookie['path'] = path
    for k, v in kwargs.iteritems():
        if 'max_age' == k:
            k = 'max-age'
        cookie[k] = v
    return cookie


def _time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0