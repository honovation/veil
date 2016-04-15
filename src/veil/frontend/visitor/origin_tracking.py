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
from veil.frontend.web import *

LOGGER = logging.getLogger(__name__)
VEIL_VISITOR_ORIGIN_COOKIE_NAME = 'vo'
DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS = 30


def enable_visitor_origin_tracking(exclude_host_suffixes=(), exclude_path_prefixes=(), cookie_expires_days=DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS):
    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        referer = request.headers.get('Referer')
        try:
            if not request.user_agent.is_bot and request.method == 'GET':
                if referer:
                    referer = to_unicode(referer, strict=False, additional={
                        'uri': request.uri,
                        'referer': referer,
                        'remote_ip': request.remote_ip,
                        'user_agent': request.user_agent.ua_string
                    })
                    host = urlparse(referer).hostname
                    if host:
                        host = host.strip('.')
                        if not host.endswith(get_website_parent_domain(request.website)) \
                                and all(not host.endswith(host_suffix) for host_suffix in exclude_host_suffixes) \
                                and all(not request.path.startswith(to_str(path_prefix)) for path_prefix in exclude_path_prefixes):
                            set_visitor_origin(referer, expires_days=cookie_expires_days)
        except Exception:
            LOGGER.exception('failed to track visitor origin: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'uri': request.uri,
                'referer': referer,
                'remote_ip': request.remote_ip,
                'user_agent': request.user_agent.ua_string
            })
        finally:
            yield

    return f


def set_visitor_origin(referer=None, cps=None, cps_detail=None, expires_days=DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS):
    value = '|'.join((referer or '', unicode(cps) if cps else '', cps_detail or ''))
    set_secure_cookie(name=VEIL_VISITOR_ORIGIN_COOKIE_NAME, value=value, expires_days=expires_days)


def get_visitor_origin(cps_as_int=False, max_age_days=DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS):
    cookie = get_secure_cookie(VEIL_VISITOR_ORIGIN_COOKIE_NAME, max_age_days=max_age_days)
    if not cookie:
        return None, None, None, None
    try:
        referer, cps, cps_detail = cookie.split('|', 2)
        if referer and cps and referer in cps: # backward compatibility: host in cookie
            host, referer, cps, cps_detail = cookie.split('|', 3)
        else:
            host = urlparse(referer).hostname
            if host:
                host = host.strip('.')
        host = host or None
        referer = referer or None
        if cps_as_int:
            try:
                cps = int(cps)
            except (TypeError, ValueError):
                cps = None
        else:
            cps = cps or None
        cps_detail = cps_detail or None
    except Exception:
        LOGGER.warn('invalid visitor origin tracking cookie: %(cookie)s', {'cookie': cookie})
        return None, None, None, None
    return host, referer, cps, cps_detail
