"""
Track visitor origin in cookie, origins includes:
    veil tracking method: vtm_channel (marketing channel ID), vtm_term (marketing keyword)
    HTTP referrer
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
    exclude_path_prefixes = tuple(to_str(path_prefix) for path_prefix in exclude_path_prefixes)

    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        referrer = request.headers.get('Referer')
        try:
            if not request.user_agent.is_bot and request.method == 'GET':
                vtm_channel = get_http_argument('vtm_channel', optional=True)
                vtm_term = get_http_argument('vtm_term', optional=True) if vtm_channel else None
                record_referrer = False
                if referrer:
                    referrer = to_unicode(referrer, strict=False, additional={
                        'uri': request.uri,
                        'referer': referrer,
                        'remote_ip': request.remote_ip,
                        'user_agent': request.user_agent.ua_string
                    })
                    host = urlparse(referrer).hostname
                    if host:
                        host = host.strip('.')
                        if not host.endswith(get_website_parent_domain(request.website)) \
                                and all(not host.endswith(host_suffix) for host_suffix in exclude_host_suffixes) \
                                and all(not request.path.startswith(path_prefix) for path_prefix in exclude_path_prefixes):
                            record_referrer = True
                if vtm_channel or record_referrer:
                    set_visitor_origin(vtm_channel, vtm_term, referrer if record_referrer else None, expires_days=cookie_expires_days)
        except Exception:
            LOGGER.exception('failed to track visitor origin: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'uri': request.uri,
                'referer': referrer,
                'remote_ip': request.remote_ip,
                'user_agent': request.user_agent.ua_string
            })
        finally:
            yield

    return f


def set_visitor_origin(vtm_channel=None, vtm_term=None, referrer=None, expires_days=DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS):
    value = '|'.join((vtm_channel or '', vtm_term or '', referrer or ''))
    set_secure_cookie(name=VEIL_VISITOR_ORIGIN_COOKIE_NAME, value=value, expires_days=expires_days)


def get_visitor_origin(max_age_days=DEFAULT_ORIGIN_COOKIE_EXPIRES_DAYS):
    cookie = get_secure_cookie(VEIL_VISITOR_ORIGIN_COOKIE_NAME, max_age_days=max_age_days)
    if not cookie:
        return None, None, None
    try:
        vtm_channel, vtm_term, referrer = cookie.split('|', 2)
        if vtm_channel:  # TODO: remove after 2016-05-25
            try:
                int(vtm_channel)
            except Exception:
                return None, None, None
    except Exception:
        LOGGER.warn('invalid visitor origin tracking cookie: %(cookie)s', {'cookie': cookie})
        return None, None, None
    else:
        return vtm_channel or None, vtm_term or None, referrer or None
