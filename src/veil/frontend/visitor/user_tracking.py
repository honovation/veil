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
from veil.model.collection import *
from veil.frontend.nginx import *
from veil.frontend.web import *
from veil.utility.http import *

LOGGER = logging.getLogger(__name__)
redis = register_redis('persist_store')

VEIL_SECURED_USER_CODE_COOKIE_DEFAULT_NAME = '{}S'.format(VEIL_USER_CODE_COOKIE_NAME)
DEFAULT_COOKIE_EXPIRES_DAYS = 360
DEFAULT_SESSION_TTL = timedelta(minutes=30)
SESSION_TTL_ENABLED = lambda: True

config = {}  # one process services at most one website, i.e. a specific purpose


def enable_user_tracking(purpose, try_sign_in=None, login_url='/login', session_ttl=DEFAULT_SESSION_TTL, is_session_ttl_enabled=SESSION_TTL_ENABLED,
                         session_cookie_on_parent_domain=False, cookie_expires_days=DEFAULT_COOKIE_EXPIRES_DAYS,
                         secured_user_code_cookie_name=VEIL_SECURED_USER_CODE_COOKIE_DEFAULT_NAME, secured_user_code_cookie_on_parent_domain=False):
    config[purpose] = DictObject(login_url=login_url, session_ttl=session_ttl, is_session_ttl_enabled=is_session_ttl_enabled,
                                 session_cookie_on_parent_domain=session_cookie_on_parent_domain, cookie_expires_days=cookie_expires_days,
                                 secured_user_code_cookie_name=secured_user_code_cookie_name,
                                 secured_user_code_cookie_on_parent_domain=secured_user_code_cookie_on_parent_domain)

    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        request.tracking_code = get_browser_code()
        try:
            if request.user_agent.is_bot:
                if TAG_NO_LOGIN_REQUIRED not in request.route.tags:
                    set_http_status_code(httplib.FORBIDDEN)
                    end_http_request_processing()
            else:
                if not request.tracking_code:
                    request.tracking_code = uuid.uuid4().get_hex()
                set_browser_code(request.website, request.tracking_code)

                if try_sign_in:
                    try_sign_in()

                latest_user_id = get_latest_user_id(request.website)
                if latest_user_id:
                    set_latest_user_id(request.website, latest_user_id)

                session = get_user_session(request.website, request.tracking_code)
                if session:
                    refresh_user_session_ttl(session)

                if TAG_NO_LOGIN_REQUIRED not in request.route.tags and not (session and get_logged_in_user_id(request.website, session)):
                    if request.method in {'GET', 'HEAD'}:
                        return_url = request.uri
                    else:
                        return_url = request.referrer.raw
                    if not return_url:
                        return_url = '/'
                    current_login_url = '{}{}ru={}'.format(config[request.website].login_url, '&' if '?' in config[request.website].login_url else '?',
                                                           quote_plus(return_url))
                    if request.is_ajax:
                        set_http_status_code(httplib.UNAUTHORIZED)
                        get_current_http_response().set_header('WWW-Authenticate', current_login_url)
                        end_http_request_processing()
                    else:
                        redirect_to(current_login_url)
        except HTTPError:
            raise
        except Exception:
            LOGGER.exception('failed to track user: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'uri': request.uri,
                'referer': request.referrer.raw,
                'remote_ip': request.remote_ip,
                'user_agent': request.user_agent.ua_string
            })
        yield

    return f


def enable_access_to_external_cookie(purpose, name, max_age_days):
    """
    A use case: op places order on behalf of shopper
        When an op log on website op, record a cookie on parent domain.
        Website shopper process need be enabled with access to op cookie so that it could check the op cookie to get the current op
    :param purpose:
    :param name:
    :param max_age_days:
    :return:
    """
    config.setdefault(purpose, DictObject()).update(dict(secured_user_code_cookie_name=name, cookie_expires_days=max_age_days))


def get_browser_code():
    return get_cookie(VEIL_BROWSER_CODE_COOKIE_NAME)


def set_browser_code(purpose, browser_code):
    set_cookie(name=VEIL_BROWSER_CODE_COOKIE_NAME, value=browser_code, expires_days=config[purpose].cookie_expires_days,
               domain=get_website_parent_domain(purpose))


def get_latest_user_id(purpose=None, max_age_days=None):
    if purpose is None:
        purpose = get_current_http_request().website
    purpose_config = config[purpose]
    return get_secure_cookie(purpose_config.secured_user_code_cookie_name, max_age_days=max_age_days or purpose_config.cookie_expires_days)


def set_latest_user_id(purpose, user_id):
    domain = get_website_parent_domain(purpose) if config[purpose].secured_user_code_cookie_on_parent_domain else None
    set_secure_cookie(name=config[purpose].secured_user_code_cookie_name, value=user_id, expires_days=config[purpose].cookie_expires_days, domain=domain)
    set_cookie(name=VEIL_USER_CODE_COOKIE_NAME, value=user_id, expires_days=config[purpose].cookie_expires_days, domain=None)


def get_user_session(purpose, browser_code=None):
    session_value = get_secure_cookie(purpose)
    if session_value:
        try:
            session_purpose, session_browser_code, session_user_id = session_value.split('|', 2)
        except Exception:
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


def get_logged_in_user_id(purpose=None, session=None, is_session_ttl_enabled=None):
    """
    a special case is to get the user of website B from website A
    """
    if purpose is None:
        purpose = get_current_http_request().website
    assert purpose in config and (not session or session.purpose == purpose)
    session = session or get_user_session(purpose)
    if not session:
        return None
    is_session_ttl_enabled = is_session_ttl_enabled or config[purpose].is_session_ttl_enabled
    if is_session_ttl_enabled():
        user_id = redis().get(logged_in_user_id_key(session))
        if not user_id or user_id != session.user_id:
            return None
    return session.user_id


def remember_logged_in_user_id(user_id, browser_code=None):
    purpose = get_current_http_request().website
    user_id = unicode(user_id)
    session = set_user_session(purpose, browser_code or get_browser_code(), user_id)
    if config[purpose].is_session_ttl_enabled():
        redis().setex(logged_in_user_id_key(session), config[purpose].session_ttl, user_id)
    if get_latest_user_id(purpose) != user_id:
        set_latest_user_id(purpose, user_id)


def remove_logged_in_user_id(purpose=None, session=None, browser_code=None):
    if purpose is None:
        purpose = get_current_http_request().website
    if config[purpose].is_session_ttl_enabled():
        session = session or get_user_session(purpose, browser_code)
        if session:
            redis().delete(logged_in_user_id_key(session))
    clear_user_session(purpose)


def remove_logged_in_user_ids(purpose):
    count = redis().del_per_pattern('lu:{}:*'.format(purpose), 2000)
    LOGGER.info('kicked logged-in users out: %(purpose)s, %(count)s', {'purpose': purpose, 'count': count})
    return count


def logged_in_user_id_key(session):
    return 'lu:{}:{}'.format(session.purpose, session.browser_code)
