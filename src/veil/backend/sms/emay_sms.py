# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import socket
from time import sleep
import urllib2
import urllib
import logging
import re
import sys
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
    exception = None
    tries = 0
    max_tries = 2
    while tries < max_tries:
        tries += 1
        if tries > 1:
            sleep(10)
        try:
            response = urllib2.urlopen(SEND_SMS_URL, data=urllib.urlencode(data), timeout=http_timeout).read()
        except Exception as e:
            exception = e
            if isinstance(e, urllib2.HTTPError):
                LOGGER.exception('sms sending service cannot fulfill the request: %(send_sms_url)s', {
                    'send_sms_url': SEND_SMS_URL
                })
                if 400 <= e.code < 500: # 4xx, client error, no retry
                    break
            elif isinstance(e, socket.timeout) or isinstance(e, urllib2.URLError) and isinstance(e.reason, socket.timeout):
                LOGGER.exception('sms sending service timed out: %(timeout)s, %(send_sms_url)s', {
                    'timeout': http_timeout,
                    'send_sms_url': SEND_SMS_URL
                })
            elif isinstance(e, urllib2.URLError):
                LOGGER.exception('cannot reach sms sending service: %(send_sms_url)s', {
                    'send_sms_url': SEND_SMS_URL
                })
            else:
                LOGGER.exception('exception occurred while sending sms: : %(send_sms_url)s', {
                    'send_sms_url': SEND_SMS_URL
                })
        else:
            exception = None
            break
    if exception is None:
        return_value = get_return_value(response)
        if return_value == 0:
            LOGGER.info('succeeded to send sms: %(sms_code)s, %(receivers)s', {
                'sms_code': sms_code,
                'receivers': receivers
            })
        else:
            raise Exception('failed to send sms with bad value returned: {}, {}, {}'.format(response, sms_code, receivers))
    else:
        LOGGER.exception('failed to send sms: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
        raise exception, None, sys.exc_info()[2]
