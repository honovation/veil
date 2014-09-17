# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
import requests
from veil_component import VEIL_ENV_TYPE
from veil.environment import get_application_sms_whitelist
from veil.backend.queue import *
from .emay_sms_client_installer import emay_sms_client_config

LOGGER = logging.getLogger(__name__)

SEND_SMS_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 500 # 500 Chinese or 1000 English chars


@job('send_transactional_sms', retry_every=10, retry_timeout=90)
def send_transactional_sms_job(receiver, message, sms_code):
    send_sms(receiver, message, sms_code)


def send_sms(receivers, message, sms_code):
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
        #TODO: retry at most 2 times upon connection timeout or 500 errors, back-off 3 seconds (avoid IP blocking due to too frequent queries) when new-version requests supports
        response = requests.post(SEND_SMS_URL, data=data, timeout=(3.05, 9))
        response.raise_for_status()
    except:
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


def get_return_value(xml):
    result = re.findall('<error>(\d)</error>', xml)
    return int(result[0]) if result else None
