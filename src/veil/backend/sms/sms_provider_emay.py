# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import re
from decimal import Decimal
from math import ceil
from veil.profile.installer import *
from veil.utility.encoding import *
from veil.utility.http import *
from veil.backend.sms.sms import SMService, SendError

LOGGER = logging.getLogger(__name__)

SMS_PROVIDER_ID = 1
SEND_SMS_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action'
QUERY_BALANCE_URL = 'http://sdkhttp.eucp.b2m.cn/sdkproxy/querybalance.action'
MAX_SMS_RECEIVERS = 200
MAX_SMS_CONTENT_LENGTH = 500  # 500 Chinese or 1000 English chars
MAX_LENGTH_PER_MESSAGE = 70
OVER_MAX_LENGTH_MESSAGE_LENGTH_PER_MESSAGE = MAX_LENGTH_PER_MESSAGE

PATTERN_FOR_ERROR = re.compile('<error>(\d+?)</error>')
PATTERN_FOR_MESSAGE = re.compile('<message>(\d+\.?\d)</message>')

_config = None


def register():
    add_application_sub_resource('emay_sms_client', lambda config: emay_sms_client_resource(**config))
    return EmaySMService(SMS_PROVIDER_ID)


@composite_installer
def emay_sms_client_resource(cdkey, password):
    return [file_resource(path=VEIL_ETC_DIR / 'emay-sms-client.cfg', content=render_config('emay-sms-client.cfg.j2', cdkey=cdkey, password=password))]


def load_emay_sms_client_config():
    return load_config_from(VEIL_ETC_DIR / 'emay-sms-client.cfg', 'cdkey', 'password')


def emay_sms_client_config():
    global _config
    if _config is None:
        _config = load_emay_sms_client_config()
    return _config


class EmaySMService(SMService):
    def __init__(self, sms_provider_id):
        super(EmaySMService, self).__init__(sms_provider_id, MAX_SMS_RECEIVERS)
        self.config = emay_sms_client_config()

    def send(self, receivers, message, sms_code, transactional, promotional=False):
        LOGGER.debug('attempt to send sms: %(sms_code)s, %(receivers)s, %(message)s', {'sms_code': sms_code, 'receivers': receivers, 'message': message})
        receivers = set(r.strip() for r in receivers if r.strip())
        if len(message) > MAX_SMS_CONTENT_LENGTH:
            raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
        receivers = ','.join(receivers)
        message = to_str(message)
        data = {'cdkey': self.config.cdkey, 'password': self.config.password, 'phone': receivers, 'message': message}
        try:
            response = requests.post(SEND_SMS_URL, data=data, timeout=(3.05, 9),
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
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
            LOGGER.exception('emay sms send exception-thrown: %(sms_code)s, %(receivers)s, %(message)s', {
                'sms_code': sms_code,
                'receivers': receivers,
                'message': e.message
            })
            raise
        else:
            return_value = get_return_value(response.text)
            if return_value == 0:
                LOGGER.info('emay sms send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            else:
                LOGGER.error('emay sms send failed: %(sms_code)s, %(response)s, %(receivers)s', {
                    'sms_code': sms_code, 'response': response.text, 'receivers': receivers
                })
                # TODO: need verify latest interface for multiple receiver and partial failed
                raise SendError('emay sms send failed: {}, {}, {}'.format(sms_code, response.text, receivers), receivers.split(','))

    def query_balance(self):
        if not self.config:
            self.config = emay_sms_client_config()
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

    def get_minimal_message_quantity(self, message):
        message_length = len(message)
        if message_length < MAX_LENGTH_PER_MESSAGE:
            return 1
        return int(ceil(message_length/OVER_MAX_LENGTH_MESSAGE_LENGTH_PER_MESSAGE))


def get_return_value(xml):
    m = PATTERN_FOR_ERROR.search(xml)
    return int(m.group(1)) if m else None


def get_return_message(xml):
    m = PATTERN_FOR_MESSAGE.search(xml)
    return Decimal(m.group(1)) if m else None
