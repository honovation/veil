from __future__ import unicode_literals, print_function, division
from datetime import timedelta
import httplib
import logging
import contextlib
import uuid
from veil.backend.redis import *
from veil.development.test import *
from veil.utility.http import *
from veil.frontend.nginx import *
from veil.frontend.web import *

LOGGER = logging.getLogger(__name__)
redis = register_redis('persist_store')

VEIL_SECURED_BROWSER_CODE_COOKIE_NAME = '{}S'.format(VEIL_BROWSER_CODE_COOKIE_NAME)
VEIL_SECURED_USER_CODE_COOKIE_NAME = '{}S'.format(VEIL_USER_CODE_COOKIE_NAME)
DEFAULT_COOKIE_EXPIRES_DAYS = 360
DEFAULT_SESSION_TIMEOUT = timedelta(minutes=30)


def enable_user_tracking(purpose, login_url='/login', session_timeout=DEFAULT_SESSION_TIMEOUT, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        try:
            parent_domain = get_website_parent_domain(purpose)
            current_route = get_current_http_context().route
            if is_web_spider(request.headers.get('User-Agent')):
                if TAG_NO_LOGIN_REQUIRED not in current_route.tags:
                    set_http_status_code(httplib.FORBIDDEN)
                    end_http_request_processing()
            else:
                browser_code = get_browser_code(cookie_expires_days)
                new_browser_code = browser_code or uuid.uuid4().get_hex()
                set_browser_code(new_browser_code, cookie_expires_days, parent_domain)

                latest_user_id = get_latest_user_id(cookie_expires_days)
                if latest_user_id:
                    set_latest_user_id(latest_user_id, cookie_expires_days)
                    if browser_code:
                        refresh_user_session_timeout(purpose, browser_code, session_timeout)

                if TAG_NO_LOGIN_REQUIRED not in current_route.tags and not (browser_code and is_user_logged_in(purpose, browser_code=browser_code)):
                    if request.method.upper() == 'GET':
                        login_referer = request.uri
                    else:
                        login_referer = request.headers.get('Referer')
                    if login_referer:
                        remember_user_login_referer(purpose, login_referer, session_timeout, browser_code=new_browser_code)
                    redirect_to(login_url)
        except HTTPError:
            raise
        except:
            LOGGER.exception('failed to track user: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'uri': request.uri,
                'referer': request.headers.get('Referer'),
                'remote_ip': request.remote_ip,
                'user_agent': request.headers.get('User-Agent')
            })
        yield
    return f


def get_browser_code(cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    if get_executing_test(optional=True):
        return 'BROWSER_CODE_FOR_TEST_ENV'
    return get_secure_cookie(VEIL_SECURED_BROWSER_CODE_COOKIE_NAME, max_age_days=cookie_expires_days)


def set_browser_code(browser_code, cookie_expires_days, browser_cookie_domain):
    set_secure_cookie(name=VEIL_SECURED_BROWSER_CODE_COOKIE_NAME, value=browser_code, expires_days=cookie_expires_days, domain=browser_cookie_domain)
    set_cookie(name=VEIL_BROWSER_CODE_COOKIE_NAME, value=browser_code, expires_days=cookie_expires_days, domain=browser_cookie_domain)


def get_latest_user_id(cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    return get_secure_cookie(VEIL_SECURED_USER_CODE_COOKIE_NAME, max_age_days=cookie_expires_days)


def set_latest_user_id(user_id, cookie_expires_days):
    set_secure_cookie(name=VEIL_SECURED_USER_CODE_COOKIE_NAME, value=user_id, expires_days=cookie_expires_days, domain=None)
    set_cookie(name=VEIL_USER_CODE_COOKIE_NAME, value=user_id, expires_days=cookie_expires_days, domain=None)


def refresh_user_session_timeout(purpose, browser_code, session_timeout):
    redis().expire(logged_in_user_id_key(purpose, browser_code), session_timeout)


def is_user_logged_in(purpose, browser_code=None, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    return redis().exists(logged_in_user_id_key(purpose, browser_code))


def get_logged_in_user_id(purpose, browser_code=None, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    return redis().get(logged_in_user_id_key(purpose, browser_code))


def remember_logged_in_user_id(purpose, user_id, session_timeout=DEFAULT_SESSION_TIMEOUT, browser_code=None,
        cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    redis().setex(logged_in_user_id_key(purpose, browser_code), session_timeout, user_id)
    if get_latest_user_id(cookie_expires_days) != unicode(user_id):
        set_latest_user_id(user_id, cookie_expires_days)


def remove_logged_in_user_id(purpose, browser_code=None, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    redis().delete(logged_in_user_id_key(purpose, browser_code))


def remember_user_login_referer(purpose, login_referer, session_timeout=DEFAULT_SESSION_TIMEOUT, browser_code=None,
        cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    redis().setex(login_referer_key(purpose, browser_code), session_timeout, login_referer)


def get_user_login_referer(purpose, browser_code=None, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    return redis().get(login_referer_key(purpose, browser_code))


def remove_user_login_referer(purpose, browser_code=None, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    browser_code = browser_code or get_browser_code(cookie_expires_days)
    redis().delete(login_referer_key(purpose, browser_code))


def logged_in_user_id_key(purpose, browser_code):
    return 'lu:{}:{}'.format(purpose, browser_code)


def login_referer_key(purpose, browser_code):
    return 'lr:{}:{}'.format(purpose, browser_code)
