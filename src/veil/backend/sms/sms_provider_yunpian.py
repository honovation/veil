# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from .sms import SMService, SendError, NotConfigured
from veil.model.collection import *
from veil.utility.http import *
from veil.utility.misc import *
from .yunpian_sms_client_installer import yunpian_sms_client_config

LOGGER = logging.getLogger(__name__)

SMS_PROVIDER_ID = 2
SEND_SMS_URL = 'http://yunpian.com/v1/sms/send.json'
QUERY_BALANCE_URL = 'http://yunpian.com/v1/user/get.json'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 400


def get_yunpian_smservice_instance():
    return YunpianSMService(SMS_PROVIDER_ID)


class YunpianSMService(SMService):
    def __init__(self, sms_provider_id):
        super(YunpianSMService, self).__init__(sms_provider_id)
        self.config = None

    def get_receiver_list(self, receivers):
        if isinstance(receivers, basestring):
            receivers = [receivers]
        return [r for r in chunks(receivers, MAX_SMS_RECEIVERS)]

    def send(self, receivers, message, sms_code, transactional):
        if not self.config:
            self.config = yunpian_sms_client_config()
        LOGGER.debug('attempt to send sms: %(sms_code)s, %(receivers)s, %(message)s', {'sms_code': sms_code, 'receivers': receivers, 'message': message})
        receivers = set(r.strip() for r in receivers if r.strip())
        if len(message) > MAX_SMS_CONTENT_LENGTH:
            raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
        receivers = ','.join(receivers)
        message = message.encode('UTF-8')
        data = {'apikey': self.config.apikey, 'mobile': receivers, 'text': message}
        try:
            # retry at most 2 times upon connection timeout or 500 errors, back-off 2 seconds (avoid IP blocking due to too frequent queries)
            response = requests.post(SEND_SMS_URL, data=data, timeout=(3.05, 9), headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'},
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist=[503], backoff_factor=2))
            response.raise_for_status()
        except ReadTimeout:
            if transactional:
                LOGGER.exception('yunpian sms send ReadTimeout exception for transactional message: %(sms_code)s, %(receivers)s',
                                 {'sms_code': sms_code, 'receivers': receivers})
                raise
            else:
                LOGGER.exception('yunpian sms send ReadTimeout exception for marketing message: %(sms_code)s, %(receivers)s',
                                 {'sms_code': sms_code, 'receivers': receivers})
        except Exception as e:
            LOGGER.exception('yunpian sms send exception-thrown: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            raise SendError(e.message)
        else:
            result = objectify(response.json())
            if result.code == 0:
                LOGGER.info('yunpian sms send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            else:
                LOGGER.error('yunpian sms send failed: %(sms_code)s, %(response)s, %(receivers)s', {
                    'sms_code': sms_code, 'response': response.text, 'receivers': receivers
                })
                raise SendError('yunpian sms send failed: {}, {}, {}'.format(sms_code, response.text, receivers))

    def query_balance(self):
        if not self.config:
            self.config = yunpian_sms_client_config()
        if not self.config.apikey:
            raise NotConfigured()
        data = {'apikey': self.config.apikey}
        try:
            response = requests.post(QUERY_BALANCE_URL, data=data, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
            response.raise_for_status()
        except Exception:
            LOGGER.exception('yunpian query balance exception-thrown')
            raise
        else:
            result = objectify(response.json())
            if result.code != 0:
                LOGGER.error('yunpian query balance failed: %(response)s', {'response': response.text})
                raise Exception('yunpian query balance failed: {}'.format(response.text))
            else:
                balance = result.user.balance
                if balance is None:
                    LOGGER.error('yunpian query balance got invalid balance: %(response)s', {'response': response.text})
                    raise Exception('yunpian query balance got invalid balance: {}'.format(response.text))
                return balance
