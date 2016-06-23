# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from math import ceil
from veil.profile.installer import *
from veil.model.collection import *
from veil.utility.http import *
from veil.utility.misc import *
from .sms import SMService, SendError

LOGGER = logging.getLogger(__name__)

SMS_PROVIDER_ID = 2
SEND_SMS_URL = 'https://sms.yunpian.com/v2/sms/batch_send.json'
SINGLE_SEND_SMS_URL = 'https://sms.yunpian.com/v2/sms/single_send.json'
SEND_VOICE_URL = 'https://voice.yunpian.com/v2/voice/send.json'
QUERY_BALANCE_URL = 'https://sms.yunpian.com/v2/user/get.json'
MAX_SMS_RECEIVERS = 1000
MAX_SMS_CONTENT_LENGTH = 400
MAX_LENGTH_PER_MESSAGE = 70
OVER_MAX_LENGTH_MESSAGE_LENGTH_PER_MESSAGE = 67

IGNORE_CODES = {
    8,   # 同一手机号30秒内重复提交相同的内容
    9,   # 同一手机号5分钟内重复提交相同的内容超过3次
    10,  # 手机号黑名单过滤
    17,  # 24小时内同一手机号发送次数超过限制
    22   # 1小时内同一手机号发送次数超过限制
}
RETRY_CODES = {
    -5,   # 访问频率超限
    -50,  # 未知异常
    -51,  # 系统繁忙
    -53   # 提交短信失败
}

_config = None


def register():
    add_application_sub_resource('yunpian_sms_client', lambda config: yunpian_sms_client_resource(**config))
    return get_yunpian_smservice_instance()


@composite_installer
def yunpian_sms_client_resource(apikey, promotion_apikey=None):
    return [
        file_resource(path=VEIL_ETC_DIR / 'yunpian-sms-client.cfg',
                      content=render_config('yunpian-sms-client.cfg.j2', apikey=apikey, promotion_apikey=promotion_apikey))
    ]


def load_yunpian_sms_client_config():
    return load_config_from(VEIL_ETC_DIR / 'yunpian-sms-client.cfg', 'apikey')


def yunpian_sms_client_config():
    global _config
    if _config is None:
        _config = load_yunpian_sms_client_config()
    return _config


def get_yunpian_smservice_instance():
    return YunpianSMService(SMS_PROVIDER_ID)


class YunpianSMService(SMService):
    def __init__(self, sms_provider_id):
        super(YunpianSMService, self).__init__(sms_provider_id, support_voice=True)
        self.config = None

    def get_receiver_list(self, receivers):
        if isinstance(receivers, basestring):
            receivers = [receivers]
        return [r for r in chunks(receivers, MAX_SMS_RECEIVERS)]

    def single_send(self, receiver, message, sms_code, transactional, promotional=False):
        if not self.config:
            self.config = yunpian_sms_client_config()
        api_key = self.config.apikey if not promotional else self.config.promotion_apikey
        message = message.encode('UTF-8')
        data = {'apikey': api_key, 'mobile': receiver, 'text': message}
        response = None
        try:
            # retry at most 2 times upon connection timeout or 500 errors, back-off 2 seconds (avoid IP blocking due to too frequent queries)
            response = requests.post(SINGLE_SEND_SMS_URL, data=data, timeout=(3.05, 9),
                                     headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'},
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
            response.raise_for_status()
        except ReadTimeout:
            if transactional:
                LOGGER.exception('yunpian sms send ReadTimeout exception for transactional message: %(sms_code)s, %(receiver)s',
                                 {'sms_code': sms_code, 'receiver': receiver})
                raise
            else:
                LOGGER.exception('yunpian sms send ReadTimeout exception for marketing message: %(sms_code)s, %(receiver)s',
                                 {'sms_code': sms_code, 'receiver': receiver})
        except Exception as e:
            LOGGER.exception('yunpian sms send exception-thrown: %(sms_code)s, %(receiver)s, %(message)s, %(response)s', {
                'sms_code': sms_code, 'receiver': receiver, 'message': e.message, 'response': response.text if response else ''
            })
            if response and response.status_code == 400:
                result = objectify(response.json())
                if result.code in IGNORE_CODES:
                    return
            raise
        else:
            result = objectify(response.json())
            if result.code == 0:
                LOGGER.info('yunpian sms send succeeded: %(sms_code)s, %(receiver)s', {'sms_code': sms_code, 'receiver': receiver})
            else:
                LOGGER.error('yunpian sms send failed: %(sms_code)s, %(response)s, %(receiver)s', {
                    'sms_code': sms_code, 'response': response.text, 'receiver': receiver
                })
                retry_mobiles = [receiver] if result.code in RETRY_CODES else []
                raise SendError('yunpian sms send failed: {}, {}'.format(sms_code, receiver), retry_mobiles)

    def send(self, receivers, message, sms_code, transactional, promotional=False):
        for receiver in receivers:
            self.single_send(receiver, message, sms_code, transactional, promotional=promotional)
    
    def batch_send(self, receivers, message, sms_code, transactional, promotional=False):
        if not self.config:
            self.config = yunpian_sms_client_config()
        api_key = self.config.apikey if not promotional else self.config.promotion_apikey
        LOGGER.debug('attempt to send sms: %(sms_code)s, %(receivers)s, %(message)s', {'sms_code': sms_code, 'receivers': receivers, 'message': message})
        receivers = set(r.strip() for r in receivers if r.strip())
        if len(message) > MAX_SMS_CONTENT_LENGTH:
            raise Exception('try to send sms with message size over {}'.format(MAX_SMS_CONTENT_LENGTH))
        receivers = ','.join(receivers)
        message = message.encode('UTF-8')
        data = {'apikey': api_key, 'mobile': receivers, 'text': message}
        response = None
        try:
            # retry at most 2 times upon connection timeout or 500 errors, back-off 2 seconds (avoid IP blocking due to too frequent queries)
            response = requests.post(SEND_SMS_URL, data=data, timeout=(3.05, 9), headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'},
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
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
            LOGGER.exception('yunpian sms send exception-thrown: %(sms_code)s, %(receivers)s, %(message)s, %(response)s', {
                'sms_code': sms_code, 'receivers': receivers, 'message': e.message, 'response': response.text if response else ''
            })
            if response and response.status_code == 400:
                result = objectify(response.json())
                if result.code in IGNORE_CODES:
                    return
            raise
        else:
            result = objectify(response.json())
            if all(r.code == 0 for r in result.data):
                LOGGER.info('yunpian sms send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receivers': receivers})
            else:
                LOGGER.error('yunpian sms send failed: %(sms_code)s, %(response)s, %(receivers)s', {
                    'sms_code': sms_code, 'response': response.text, 'receivers': receivers
                })
                retry_mobiles = set(r.mobile for r in result.data if r.code in RETRY_CODES)
                raise SendError('yunpian sms send failed: {}, {}'.format(sms_code, receivers), retry_mobiles)

    def send_voice(self, receiver, code, sms_code):
        if not self.config:
            self.config = yunpian_sms_client_config()
        LOGGER.debug('attempt to send voice: %(sms_code)s, %(receiver)s, %(message)s', {'sms_code': sms_code, 'receiver': receiver, 'code': code})
        data = {'apikey': self.config.apikey, 'mobile': receiver, 'code': code}
        response = None
        try:
            # retry at most 2 times upon connection timeout or 500 errors, back-off 2 seconds (avoid IP blocking due to too frequent queries)
            response = requests.post(SEND_VOICE_URL, data=data, timeout=(3.05, 9), headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'},
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
            response.raise_for_status()
        except ReadTimeout:
                LOGGER.exception('yunpian voice send ReadTimeout exception for transactional message: %(sms_code)s, %(receiver)s',
                                 {'sms_code': sms_code, 'receiver': receiver})
                raise
        except Exception as e:
            LOGGER.exception('yunpian voice send exception-thrown: %(sms_code)s, %(receiver)s, %(message)s, %(response)s', {
                'sms_code': sms_code, 'receiver': receiver, 'message': e.message, 'response': response.text if response else ''
            })
            raise
        else:
            result = objectify(response.json())
            if result.count == 1:
                LOGGER.info('yunpian voice send succeeded: %(sms_code)s, %(receivers)s', {'sms_code': sms_code, 'receiver': receiver})
            else:
                LOGGER.error('yunpian voice send failed: %(sms_code)s, %(response)s, %(receiver)s', {
                    'sms_code': sms_code, 'response': response.text, 'receiver': receiver
                })
                raise SendError('yunpian sms send failed: {}, {}'.format(sms_code, receiver), receiver)

    def query_balance(self):
        if not self.config:
            self.config = yunpian_sms_client_config()
        data = {'apikey': self.config.apikey}
        response = None
        try:
            response = requests.post(QUERY_BALANCE_URL, data=data, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
            response.raise_for_status()
        except Exception:
            LOGGER.exception('yunpian query balance exception-thrown: %(response)s', {'response': response.text if response else ''})
            raise
        else:
            result = objectify(response.json())
            balance = result.balance
            if balance is None:
                LOGGER.error('yunpian query balance got invalid balance: %(response)s', {'response': response.text})
                raise Exception('yunpian query balance got invalid balance')
            return balance

    def get_minimal_message_quantity(self, message):
        message_length = len(message)
        if message_length < MAX_LENGTH_PER_MESSAGE:
            return 1
        return int(ceil(message_length/OVER_MAX_LENGTH_MESSAGE_LENGTH_PER_MESSAGE))
