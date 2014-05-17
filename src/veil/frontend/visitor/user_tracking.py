"""
Track visitor and user

User authentication is support by user session

Purpose: identifies a website and is used to separate user sessions among different websites

Cookies:
    Browser Code: persistent cookie, visitor ID per browser on parent domain, i.e. the base domain for all websites of the VEIL Application
    User Code: persistent cookie, latest logged-in user ID on current domain, i.e. every website has its own usr code
    Session: transient cookie, indicates if the user is logged in or not, is set upon successful login
        consists of purpose, browser code and user ID and is secured
        when accessed from trustworthy environment, session ttl is disabled; otherwise enabled
        when session ttl is enabled, a redis entry with session ttl is recorded
        when the route requires login and the user is currently not logged in, redirect the user to login
            and the url to be redirected to after successful login is recorded in redis as login refer
"""
from __future__ import unicode_literals, print_function, division
from datetime import timedelta
import httplib
import logging
import contextlib
import uuid
from veil.backend.redis import *
from veil.development.test import *
from veil.model.collection import *
from veil.utility.http import *
from veil.frontend.nginx import *
from veil.frontend.web import *

LOGGER = logging.getLogger(__name__)
redis = register_redis('persist_store')

VEIL_SECURED_USER_CODE_COOKIE_NAME = '{}S'.format(VEIL_USER_CODE_COOKIE_NAME)
DEFAULT_COOKIE_EXPIRES_DAYS = 360
DEFAULT_SESSION_TTL = timedelta(minutes=30)
SESSION_TTL_ENABLED = lambda: True

config = {} # one process services at most one website, i.e. a specific purpose

def enable_user_tracking(purpose, login_url='/login', session_ttl=DEFAULT_SESSION_TTL, is_session_ttl_enabled=SESSION_TTL_ENABLED,
        session_cookie_on_parent_domain=False, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS):
    config[purpose] = DictObject(login_url=login_url, session_ttl=session_ttl, is_session_ttl_enabled=is_session_ttl_enabled,
        session_cookie_on_parent_domain=session_cookie_on_parent_domain, cookie_expires_days=cookie_expires_days)

    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        current_route = get_current_http_context().route
        try:
            if is_web_spider(request.headers.get('User-Agent')):
                if TAG_NO_LOGIN_REQUIRED not in current_route.tags:
                    set_http_status_code(httplib.FORBIDDEN)
                    end_http_request_processing()
            else:
                browser_code = get_browser_code()
                new_browser_code = browser_code or uuid.uuid4().get_hex()
                set_browser_code(purpose, new_browser_code)

                latest_user_id = get_latest_user_id(purpose)
                if latest_user_id:
                    set_latest_user_id(purpose, latest_user_id)

                session = get_user_session(purpose, new_browser_code)
                if session:
                    refresh_user_session_ttl(session)

                if TAG_NO_LOGIN_REQUIRED not in current_route.tags and not (session and get_logged_in_user_id(purpose, session)):
                    if request.method.upper() == 'GET':
                        login_referer = request.uri
                    else:
                        login_referer = request.headers.get('Referer')
                    if login_referer:
                        remember_user_login_referer(purpose, login_referer, new_browser_code)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        set_http_status_code(httplib.UNAUTHORIZED)
                        get_current_http_response().set_header('WWW-Authenticate', login_url)
                        end_http_request_processing()
                    else:
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


def get_browser_code():
    if get_executing_test(optional=True):
        return 'BROWSER_CODE_FOR_TEST_ENV'
    return get_cookie(VEIL_BROWSER_CODE_COOKIE_NAME)


def set_browser_code(purpose, browser_code):
    set_cookie(name=VEIL_BROWSER_CODE_COOKIE_NAME, value=browser_code, expires_days=config[purpose].cookie_expires_days,
        domain=get_website_parent_domain(purpose))


def get_latest_user_id(purpose):
    return get_secure_cookie(VEIL_SECURED_USER_CODE_COOKIE_NAME, max_age_days=config[purpose].cookie_expires_days)


def set_latest_user_id(purpose, user_id):
    set_secure_cookie(name=VEIL_SECURED_USER_CODE_COOKIE_NAME, value=user_id, expires_days=config[purpose].cookie_expires_days, domain=None)
    set_cookie(name=VEIL_USER_CODE_COOKIE_NAME, value=user_id, expires_days=config[purpose].cookie_expires_days, domain=None)


def get_user_session(purpose, browser_code=None):
    if get_executing_test(optional=True):
        return DictObject(purpose=purpose, browser_code=browser_code or get_browser_code(), user_id='USER_ID_FOR_TEST_ENV')
    session_value = get_secure_cookie(purpose)
    if session_value:
        try:
            session_purpose, session_browser_code, session_user_id = session_value.split('|')
        except:
            pass
        else:
            if session_purpose and session_browser_code and session_user_id and session_purpose == purpose \
                    and session_browser_code == (browser_code or get_browser_code()):
                return DictObject(purpose=session_purpose, browser_code=session_browser_code, user_id=session_user_id)
    return None


def set_user_session(purpose, browser_code, user_id):
    session = DictObject(purpose=purpose, browser_code=browser_code, user_id=user_id)
    value = '{}|{}|{}'.format(session.purpose, session.browser_code, session.user_id)
    domain = get_website_parent_domain(purpose) if config[purpose].session_cookie_on_parent_domain else None
    set_secure_cookie(name=purpose, value=value, expires_days=None, domain=domain)
    return session


def clear_user_session(purpose):
    domain = get_website_parent_domain(purpose) if config[purpose].session_cookie_on_parent_domain else None
    clear_cookie(purpose, domain=domain)


def refresh_user_session_ttl(session):
    if config[session.purpose].is_session_ttl_enabled():
        redis().expire(logged_in_user_id_key(session), config[session.purpose].session_ttl)


def get_logged_in_user_id(purpose, session=None, is_session_ttl_enabled=None):
    """
    a special case is to get the user of website B from website A
    """
    assert not session or session.purpose == purpose
    assert purpose in config or is_session_ttl_enabled is not None
    session = session or get_user_session(purpose)
    if not session:
        return None
    is_session_ttl_enabled = is_session_ttl_enabled or config[purpose].is_session_ttl_enabled
    if is_session_ttl_enabled():
        user_id = redis().get(logged_in_user_id_key(session))
        if get_executing_test(optional=True):
            return user_id
        if not user_id or user_id != session.user_id:
            return None
    return session.user_id


def remember_logged_in_user_id(purpose, user_id, browser_code=None):
    user_id = unicode(user_id)
    session = set_user_session(purpose, browser_code or get_browser_code(), user_id)
    if config[purpose].is_session_ttl_enabled():
        redis().setex(logged_in_user_id_key(session), config[purpose].session_ttl, user_id)
    if get_latest_user_id(purpose) != user_id:
        set_latest_user_id(purpose, user_id)


def remove_logged_in_user_id(purpose, session=None, browser_code=None):
    if config[purpose].is_session_ttl_enabled():
        session = session or get_user_session(purpose, browser_code)
        if session:
            redis().delete(logged_in_user_id_key(session))
    clear_user_session(purpose)


def remove_logged_in_user_ids(purpose):
    count = redis().delete_per_pattern('lu:{}:*'.format(purpose), 2000)
    LOGGER.info('kicked logged-in users out: %(purpose)s, %(count)s', {'purpose': purpose, 'count': count})
    return count


def remember_user_login_referer(purpose, login_referer, browser_code=None):
    browser_code = browser_code or get_browser_code()
    if browser_code:
        redis().setex(login_referer_key(purpose, browser_code), config[purpose].session_ttl, login_referer)


def get_user_login_referer(purpose, browser_code=None):
    browser_code = browser_code or get_browser_code()
    return redis().get(login_referer_key(purpose, browser_code)) if browser_code else None


def remove_user_login_referer(purpose, browser_code=None):
    browser_code = browser_code or get_browser_code()
    if browser_code:
        redis().delete(login_referer_key(purpose, browser_code))


def logged_in_user_id_key(session):
    return 'lu:{}:{}'.format(session.purpose, session.browser_code)


def login_referer_key(purpose, browser_code):
    return 'lr:{}:{}'.format(purpose, browser_code)
