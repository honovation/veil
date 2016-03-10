# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import logging

from veil.utility.http import *
from veil.profile.model import *
from veil_component import VEIL_ENV_TYPE

redis = register_redis('persist_store')

LOGGER = logging.getLogger(__name__)

WXMP_ACCESS_TOKEN_KEY_TPL = 'wxop:{}:wxmp-access-token'
WXMP_ACCESS_TOKEN_AUTHORIZATION_URL = 'https://api.weixin.qq.com/cgi-bin/token'


def get_wxmp_access_token(wxop_app_code, app_id, app_secret, with_ttl=False, access_token_to_refresh=None):
    if VEIL_ENV_TYPE not in {'public', 'development'}:
        raise Exception('cannot get wx access token under environment: {}'.format(VEIL_ENV_TYPE))
    if not access_token_to_refresh:
        with redis().pipeline() as pipe:
            pipe.get(WXMP_ACCESS_TOKEN_KEY_TPL.format(wxop_app_code))
            pipe.ttl(WXMP_ACCESS_TOKEN_KEY_TPL.format(wxop_app_code))
            access_token, ttl = pipe.execute()
    if access_token_to_refresh or not access_token or ttl <= 0:
        access_token, ttl = refresh_wxmp_access_token(wxop_app_code, app_id, app_secret, access_token_to_refresh or access_token)
    return DictObject(access_token=access_token, expires_in=ttl) if with_ttl else access_token


def refresh_wxmp_access_token(wxop_app_code, app_id, app_secret, access_token_to_refresh):
    with redis().lock('lock:refresh-wxmp-access-token:{}'.format(wxop_app_code), timeout=2 * 60):
        with redis().pipeline() as pipe:
            pipe.get(WXMP_ACCESS_TOKEN_KEY_TPL.format(wxop_app_code))
            pipe.ttl(WXMP_ACCESS_TOKEN_KEY_TPL.format(wxop_app_code))
            access_token, ttl = pipe.execute()
        if not access_token or ttl <= 0 or access_token == access_token_to_refresh:
            access_token, expires_in = request_wxmp_access_token(app_id, app_secret)
            ttl = expires_in - 300
            redis().setex(WXMP_ACCESS_TOKEN_KEY_TPL.format(wxop_app_code), ttl, access_token)
    return access_token, ttl


def request_wxmp_access_token(app_id, app_secret):
    params = dict(grant_type='client_credential', appid=app_id, secret=app_secret)
    try:
        response = requests.get(WXMP_ACCESS_TOKEN_AUTHORIZATION_URL, params=params, headers={'Accept': 'application/json'}, timeout=(3.05, 9),
                                max_retries=Retry(total=5, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('wxmp request access token exception-thrown')
        raise
    else:
        result = objectify(response.json())
        if hasattr(result, 'access_token'):
            LOGGER.info('wxmp request access token succeeded: %(result)s, %(appid)s', {'result': result, 'appid': params['appid']})
            return result.access_token, result.expires_in
        else:
            LOGGER.error('wxmp request access token failed: %(result)s', {'result': result})
            raise Exception('wxmp request access token failed: {}'.format(result))
