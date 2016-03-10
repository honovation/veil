# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import logging

from veil.frontend.cli import script
from veil.utility.http import *
from veil.profile.model import *
from veil_component import VEIL_ENV_TYPE

from .access_token import get_wxmp_access_token

redis = register_redis('persist_store')

LOGGER = logging.getLogger(__name__)

WXMP_JSAPI_TICKET_KEY_TPL = 'wxop:{}:wxmp-jsapi-ticket'
WXMP_JSAPI_TICKET_AUTHORIZATION_URL = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket'


def get_wxmp_jsapi_ticket(wxop_app_code, app_id, app_secret, with_ttl=False, jsapi_ticket_to_refresh=None):
    if VEIL_ENV_TYPE not in {'public', 'development'}:
        raise Exception('cannot get wx access token under environment: {}'.format(VEIL_ENV_TYPE))
    if not jsapi_ticket_to_refresh:
        with redis().pipeline() as pipe:
            pipe.get(WXMP_JSAPI_TICKET_KEY_TPL.format(wxop_app_code))
            pipe.ttl(WXMP_JSAPI_TICKET_KEY_TPL.format(wxop_app_code))
            jsapi_ticket, ttl = pipe.execute()
    if jsapi_ticket_to_refresh or not jsapi_ticket or ttl <= 0:
        access_token = get_wxmp_access_token(wxop_app_code, app_id, app_secret)
        jsapi_ticket, ttl = refresh_wxmp_jsapi_ticket(wxop_app_code, access_token, jsapi_ticket_to_refresh or jsapi_ticket)
    return DictObject(jsapi_ticket=jsapi_ticket, expires_in=ttl) if with_ttl else jsapi_ticket


def refresh_wxmp_jsapi_ticket(wxop_app_code, access_token, jsapi_ticket_to_refresh):
    with redis().lock('lock:refresh-wxmp-access-token:{}'.format(wxop_app_code), timeout=2 * 60):
        with redis().pipeline() as pipe:
            pipe.get(WXMP_JSAPI_TICKET_KEY_TPL.format(wxop_app_code))
            pipe.ttl(WXMP_JSAPI_TICKET_KEY_TPL.format(wxop_app_code))
            jsapi_ticket, ttl = pipe.execute()
        if not jsapi_ticket or ttl <= 0 or jsapi_ticket == jsapi_ticket_to_refresh:
            jsapi_ticket, expires_in = request_wxmp_jsapi_ticket(access_token)
            ttl = expires_in - 300
            redis().setex(WXMP_JSAPI_TICKET_KEY_TPL.format(wxop_app_code), ttl, jsapi_ticket)
    return jsapi_ticket, ttl


def request_wxmp_jsapi_ticket(access_token):
    params = DictObject(access_token=access_token, type='jsapi')
    try:
        response = requests.get(WXMP_JSAPI_TICKET_AUTHORIZATION_URL, params=params, headers={'Accept': 'application/json'}, timeout=(3.05, 9),
                                max_retries=Retry(total=5, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('wxmp request access token exception-thrown')
        raise
    else:
        result = objectify(response.json())
        if hasattr(result, 'ticket'):
            LOGGER.info('wxmp request access token succeeded: %(result)s, %(access_token)s', {'result': result, 'access_token': access_token})
            return result.ticket, result.expires_in
        else:
            LOGGER.error('wxmp request access token failed: %(result)s', {'result': result})
            raise Exception('wxmp request access token failed: {}'.format(result))
