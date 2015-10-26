# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
from decimal import Decimal
from veil.frontend.cli import *
from veil.utility.misc import *
from veil.utility.http import *
from .emay_sms_client_installer import emay_sms_client_config
from .sms import SMService, SendError

LOGGER = logging.getLogger(__name__)

SMS_PROVIDER_ID = 1
SEND_SMS_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action'
QUERY_BALANCE_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/querybalance.action'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 500  # 500 Chinese or 1000 English chars

PATTERN_FOR_ERROR = re.compile('<error>(\d+?)</error>')
PATTERN_FOR_MESSAGE = re.compile('<message>(\d+\.?\d)</message>')


def get_emay_smservice_instance():
    return EmaySMService(SMS_PROVIDER_ID)


class EmaySMService(SMService):
    def __init__(self, sms_provider_id):
        super(EmaySMService, self).__init__(sms_provider_id)
        self.config = emay_sms_client_config()

    def get_receiver_list(self, receivers):
        if isinstance(receivers, basestring):
            receivers = [receivers]
        return [r for r in chunks(receivers, MAX_SMS_RECEIVERS)]

    def send(self, receivers, message, sms_code, transactional):
        LOGGER.debug('attempt to send sms: %(sms_code)s, %(receivers)s, %(message)s', {'sms_code': sms_code, 'receivers': receivers, 'message': message})
        receivers = set(r.strip() for r in receivers if r.strip())
        if len(message) > MAX_SMS_CONTENT_LENGTH:
            raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
        receivers = ','.join(receivers)
        message = message.encode('UTF-8')
        data = {'cdkey': self.config.cdkey, 'password': self.config.password, 'phone': receivers, 'message': message}
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
        except Exception as e:
            LOGGER.exception('emay sms send exception-thrown: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            raise SendError(e.message)
        else:
            return_value = get_return_value(response.text)
            if return_value == 0:
                LOGGER.info('emay sms send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            else:
                LOGGER.error('emay sms send failed: %(sms_code)s, %(response)s, %(receivers)s', {
                    'sms_code': sms_code, 'response': response.text, 'receivers': receivers
                })
                raise SendError('emay sms send failed: {}, {}, {}'.format(sms_code, response.text, receivers))

    def query_balance(self):
        params = {'cdkey': self.config.cdkey, 'password': self.config.password}
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


@script('query-balance')
def query_balance_script():
    print('sms balance: {}'.format(get_emay_smservice_instance().query_balance()))


def get_return_value(xml):
    m = PATTERN_FOR_ERROR.search(xml)
    return int(m.group(1)) if m else None


def get_return_message(xml):
    m = PATTERN_FOR_MESSAGE.search(xml)
    return Decimal(m.group(1)) if m else None
