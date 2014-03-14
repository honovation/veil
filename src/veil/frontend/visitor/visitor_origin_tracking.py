# -*- coding: UTF-8 -*-
"""
Track visitor origin in cookie, origins includes:
    FIRST: uri marketing parameters, source, medium, term, campaign etc., NEED REFINE ON THIS
    SECOND: referer
    THIRD: CPS
Associate the origin with business behaviors such as user registration, orders etc.
"""

from __future__ import unicode_literals, print_function, division
import logging
import contextlib
from urlparse import urlparse
from veil.utility.encoding import *
from veil.utility.http import *
from veil.frontend.web import *

LOGGER = logging.getLogger(__name__)

VISITOR_ORIGIN_DEFAULT_COOKIE_NAME = 'vo'
VISITOR_ORIGIN_DEFAULT_COOKIE_EXPIRES_DAYS = 30


def enable_visitor_origin_tracking(cookie_name=VISITOR_ORIGIN_DEFAULT_COOKIE_NAME, cookie_expires_days=VISITOR_ORIGIN_DEFAULT_COOKIE_EXPIRES_DAYS,
        exclude_host_suffixes=(), exclude_pathe_prefixes=()):
    @contextlib.contextmanager
    def f():
        track_visitor_origin(cookie_name, cookie_expires_days, exclude_host_suffixes, exclude_pathe_prefixes)
        yield

    return f


def track_visitor_origin(cookie_name, cookie_expires_days, exclude_host_suffixes, exclude_pathe_prefixes):
    request = get_current_http_request()
    try:
        if request.method.upper() == 'GET' and not is_web_spider(request.headers.get('User-Agent')):
            referer = request.headers.get('Referer')
            if referer:
                referer = to_unicode(referer, strict=False, additional={
                    'uri': request.uri,
                    'referer': referer,
                    'remote_ip': request.remote_ip,
                    'user_agent': request.headers.get('User-Agent')
                })
                host = urlparse(referer).hostname
                if host:
                    host = host.strip('.')
                    if all(not host.endswith(host_suffix) for host_suffix in exclude_host_suffixes) \
                            and all(not request.path.startswith(path_prefix) for path_prefix in exclude_pathe_prefixes):
                        set_visitor_origin_in_cookie(cookie_name, cookie_expires_days, host, referer)
    except Exception:
        LOGGER.exception('failed to track visitor origin: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
            'uri': request.uri,
            'referer': request.headers.get('Referer'),
            'remote_ip': request.remote_ip,
            'user_agent': request.headers.get('User-Agent')
        })


def set_visitor_origin_in_cookie(name=VISITOR_ORIGIN_DEFAULT_COOKIE_NAME, expires_days=VISITOR_ORIGIN_DEFAULT_COOKIE_EXPIRES_DAYS, host=None,
        referer=None, cps=None, cps_detail=None):
    value = '|'.join((host or '', referer or '', unicode(cps) if cps else '', cps_detail or ''))
    set_secure_cookie(name=name, value=value, path='/', expires_days=expires_days)


def get_visitor_origin_from_cookie(name=VISITOR_ORIGIN_DEFAULT_COOKIE_NAME):
    cookie = get_secure_cookie(name)
    if not cookie:
        return None, None, None, None
    try:
        host, referer, cps, cps_detail = cookie.split('|', 3)
        host = host or None
        referer = referer or None
        cps = cps or None
        cps_detail = cps_detail or None
    except Exception:
        LOGGER.warn('invalid visitor origin tracking cookie: %(cookie)s', {'cookie': cookie})
        return None, None, None, None
    return host, referer, cps, cps_detail
