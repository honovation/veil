# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
from veil.utility.http import *
from .emay_sms_client_installer import emay_sms_client_config

LOGGER = logging.getLogger(__name__)

SEND_SMS_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action'
CHARSET_UTF8 = 'UTF-8'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 500 # 500 Chinese or 1000 English chars


def get_return_value(xml):
    result = re.findall('<error>(\d)</error>', xml)
    return int(result[0]) if result else None


def send_sms(receivers, message, sms_code, http_timeout=15):
    if isinstance(receivers, basestring):
        receivers = [receivers]
    receivers = [r.strip() for r in receivers if r.strip()]
    if len(receivers) > MAX_SMS_RECEIVERS:
        raise Exception('try to send sms to receivers over {}'.format(MAX_SMS_RECEIVERS))
    if len(message) > MAX_SMS_CONTENT_LENGTH:
        raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
    receivers = ','.join(receivers)
    message = message.encode(CHARSET_UTF8)
    config = emay_sms_client_config()
    data = {'cdkey': config.cdkey, 'password': config.password, 'phone': receivers, 'message': message}
    try:
        # sleep_before_retry: avoid IP blocking due to too frequent queries
        response = http_call('EMAY-SMS-SEND-API', SEND_SMS_URL, data, log_data=False, max_tries=2, sleep_before_retry=10, http_timeout=http_timeout)
    except Exception as e:
        LOGGER.exception('failed to send sms: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
        raise
    else:
        return_value = get_return_value(response)
        if return_value == 0:
            LOGGER.info('succeeded to send sms: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
        else:
            raise Exception('failed to send sms with bad value returned: {}, {}, {}'.format(response, sms_code, receivers))
