from __future__ import unicode_literals, print_function, division
import logging
import contextlib
import traceback
import operator
from veil.frontend.locale import *
from veil.frontend.web.tornado import *

LOGGER = logging.getLogger(__name__)


@contextlib.contextmanager
def install_translations(locale_provider):
    locale = locale_provider()
    if not locale:
        try:
            locale = get_browser_locale()
        except Exception:
            request = get_current_http_request()
            LOGGER.exception('failed to get browser locale: %(site)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s, %(accept_language)s\n%(stack_trace)s', {
                'site': request.host,
                'uri': request.uri,
                'referer': request.referrer.raw,
                'remote_ip': request.remote_ip,
                'user_agent': request.user_agent.ua_string,
                'accept_language': request.headers.get('Accept-Language'),
                'stack_trace': b''.join(traceback.format_stack())
            })
            locale = get_default_locale()
    with require_current_locale_being(locale):
        yield


def get_browser_locale():
    """
    Determines the user's locale from Accept-Language header.
    See http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4
    """
    request = get_current_http_request()
    if 'Accept-Language' in request.headers:
        languages = request.headers['Accept-Language'].split(',')
        locales = []
        for language in languages:
            parts = language.strip().split(';')
            if parts[0] == '*':
                continue
            if len(parts) > 1 and parts[1].startswith('q='):
                try:
                    score = float(parts[1][2:])
                except (ValueError, TypeError):
                    score = 0.0
            else:
                score = 1.0
            locales.append((parts[0], score))
        if locales:
            locales.sort(key=operator.itemgetter(1), reverse=True)
            codes = [l[0] for l in locales]
            return get_locale(*codes)
    return None
