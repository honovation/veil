# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
from decimal import Decimal
from veil.frontend.cli import script
from veil_component import VEIL_ENV_TYPE
from veil.environment import get_application_sms_whitelist
from veil.backend.queue import *
from veil.utility.http import *
from .emay_sms_client_installer import emay_sms_client_config

LOGGER = logging.getLogger(__name__)

SEND_SMS_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action'
QUERY_BALANCE_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/querybalance.action'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 500  # 500 Chinese or 1000 English chars

PATTERN_FOR_ERROR = re.compile('<error>(\d+?)</error>')
PATTERN_FOR_MESSAGE = re.compile('<message>(\d+\.?\d)</message>')


@job('send_transactional_sms', retry_every=10, retry_timeout=90)
def send_transactional_sms_job(receivers, message, sms_code):
    send_sms(receivers, message, sms_code, True)


@job('send_slow_transactional_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_slow_transactional_sms_job(receivers, message, sms_code):
    send_sms(receivers, message, sms_code, True)


@job('send_marketing_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_marketing_sms_job(receivers, message, sms_code):
    send_sms(receivers, message, sms_code, False)


def send_sms(receivers, message, sms_code, transactional):
    LOGGER.debug('attempt to send sms: %(sms_code)s, %(receivers)s, %(message)s', {'sms_code': sms_code, 'receivers': receivers, 'message': message})
    if isinstance(receivers, basestring):
        receivers = [receivers]
    receivers = set(r.strip() for r in receivers if r.strip())
    if 'public' != VEIL_ENV_TYPE:
        receivers_not_in_whitelist = set(r for r in receivers if r not in get_application_sms_whitelist())
        if receivers_not_in_whitelist:
            LOGGER.warn('Ignored sms receivers not in the whitelist under non-public env: %(receivers_not_in_whitelist)s', {
                'receivers_not_in_whitelist': receivers_not_in_whitelist
            })
            receivers -= receivers_not_in_whitelist
            if not receivers:
                return
    if len(receivers) > MAX_SMS_RECEIVERS:
        raise Exception('try to send sms to receivers over {}'.format(MAX_SMS_RECEIVERS))
    if len(message) > MAX_SMS_CONTENT_LENGTH:
        raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
    receivers = ','.join(receivers)
    message = message.encode('UTF-8')
    config = emay_sms_client_config()
    data = {'cdkey': config.cdkey, 'password': config.password, 'phone': receivers, 'message': message}
    try:
        # retry at most 2 times upon connection timeout or 500 errors, back-off 2 seconds (avoid IP blocking due to too frequent queries)
        response = requests.post(SEND_SMS_URL, data=data, timeout=(3.05, 9),
                                 max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist=[503], backoff_factor=2))
        response.raise_for_status()
    except ReadTimeout:
        if transactional:
            LOGGER.exception('emay sms send ReadTimeout exception for transactional message: %(sms_code)s, %(receivers)s',
                             {'sms_code': sms_code, 'receivers': receivers})
            raise
        else:
            LOGGER.exception('emay sms send ReadTimeout exception for marketing message: %(sms_code)s, %(receivers)s',
                             {'sms_code': sms_code, 'receivers': receivers})
    except Exception:
        LOGGER.exception('emay sms send exception-thrown: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
        raise
    else:
        return_value = get_return_value(response.text)
        if return_value == 0:
            LOGGER.info('emay sms send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
        else:
            LOGGER.error('emay sms send failed: %(sms_code)s, %(response)s, %(receivers)s', {
                'sms_code': sms_code, 'response': response.text, 'receivers': receivers
            })
            raise Exception('emay sms send failed: {}, {}, {}'.format(sms_code, response.text, receivers))


def query_balance():
    config = emay_sms_client_config()
    params = {'cdkey': config.cdkey, 'password': config.password}
    try:
        response = requests.get(QUERY_BALANCE_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('emay query balance exception-thrown')
        raise
    else:
        return_value = get_return_value(response.text)
        if return_value != 0:
            LOGGER.error('emay query balance failed: %(response)s', {'response': response.text})
            raise Exception('emay query balance failed: {}'.format(response.text))
        else:
            balance = get_return_message(response.text)
            if balance is None:
                LOGGER.error('emay query balance got invalid balance: %(response)s', {'response': response.text})
                raise Exception('emay query balance got invalid balance: {}'.format(response.text))
            return int(balance * 10)


def get_return_value(xml):
    m = PATTERN_FOR_ERROR.search(xml)
    return int(m.group(1)) if m else None


def get_return_message(xml):
    m = PATTERN_FOR_MESSAGE.search(xml)
    return Decimal(m.group(1)) if m else None
