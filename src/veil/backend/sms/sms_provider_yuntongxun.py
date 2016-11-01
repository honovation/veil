# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from hashlib import md5
from base64 import b64encode

from veil.profile.installer import *
from veil.model.collection import *
from veil.utility.clock import *
from veil.utility.encoding import *
from veil.utility.http import *
from .sms import SMService, SendError

LOGGER = logging.getLogger(__name__)

SMS_PROVIDER_ID = 3
SEND_SMS_URL_TPL = 'https://app.cloopen.com:8883/2013-12-26/Accounts/{}/SMS/TemplateSMS'
SEND_VOICE_URL_TPL = 'https://app.cloopen.com:8883/2013-12-26/Accounts/{}/Calls/VoiceVerify'
QUERY_BALANCE_URL_TPL = 'https://app.cloopen.com:8883/2013-12-26/Accounts/{}/AccountInfo'
REQUEST_SUCCESS_MARK = '000000'
MAX_SMS_RECEIVERS = 100

IGNORE_CODES = {
    '112317',  # 黑名单
    '160034',  # 黑名单
    '160039',  # 发送数量超出同模板同号天发送次数上限
    '160040',  # 验证码超出同模板同号码天发送上限
    '160041',  # 通知超出同模板同号码天发送上限
}
RETRY_CODES = {

}
BAD_REQUEST_LOG_IGNORE_CODES = {

}

_config = None


def register():
    add_application_sub_resource('yuntongxun_sms_client', lambda config: yuntongxun_sms_client_resource(**config))
    return YuntongxunSMService(SMS_PROVIDER_ID)


@composite_installer
def yuntongxun_sms_client_resource(account_sid, auth_token, app_id):
    return [
        file_resource(path=VEIL_ETC_DIR / 'yuntongxun-sms-client.cfg',
                      content=render_config('yuntongxun-sms-client.cfg.j2', account_sid=account_sid, auth_token=auth_token, app_id=app_id))
    ]


def load_yuntongxun_sms_client_config():
    return load_config_from(VEIL_ETC_DIR / 'yuntongxun-sms-client.cfg', 'account_sid', 'auth_token', 'app_id')


def yuntongxun_sms_client_config():
    global _config
    if _config is None:
        _config = load_yuntongxun_sms_client_config()
    return _config


def generate_sig():
    config = yuntongxun_sms_client_config()
    timestamp = get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S')
    return md5(to_str('{}{}{}'.format(config.account_sid, config.auth_token, timestamp))).hexdigest().upper()


def generate_request_headers():
        config = yuntongxun_sms_client_config()
        timestamp = get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S')
        return {'Accept': 'application/json',
                'Content-Type': 'application/json;charset=utf-8',
                'Authorization': b64encode(to_str('{}:{}'.format(config.account_sid, timestamp)))}


class YuntongxunSMService(SMService):
    def __init__(self, sms_provider_id):
        super(YuntongxunSMService, self).__init__(sms_provider_id, MAX_SMS_RECEIVERS, support_voice=True)

    def send(self, receivers, sms_code, transactional, promotional, message=None, template=None):
        config = yuntongxun_sms_client_config()
        need_retry_receivers = set()
        sent_receivers = set()
        for receiver in receivers:
            data = {'to': receiver, 'appId': config.app_id, 'templateId': template.id, 'datas': template.data}
            response = None
            try:
                response = requests.post(SEND_SMS_URL_TPL.format(config.account_sid), headers=generate_request_headers(), params={'sig': generate_sig()},
                                         json=data, timeout=(3.05, 9),
                                         max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
                response.raise_for_status()
            except ReadTimeout:
                LOGGER.exception('yuntongxun sms send ReadTimeout exception: %(sms_code)s, %(receiver)s', {'sms_code': sms_code, 'receiver': receiver})
                need_retry_receivers.add(receiver)
            except Exception:
                LOGGER.info('yuntongxun sms send got exception: %(response)s, %(receiver)s', {'response': response.text, 'receiver': receiver})
            else:
                try:
                    result = objectify(response.json())
                except Exception:
                    LOGGER.error('yuntongxun sms send got bad format response: %(response)s', {'response': response.text})
                    raise
                else:
                    if result.statusCode != REQUEST_SUCCESS_MARK:
                        LOGGER.error('yuntongxun sms send got failed response: %(sms_code)s, %(response)s, %(receiver)s', {
                            'sms_code': sms_code, 'response': response.text, 'receiver': receiver
                        })
                        if result.statusCode in RETRY_CODES:
                            need_retry_receivers.add(receiver)
                    else:
                        LOGGER.info('yuntongxun sms send succeeded: %(sms_code)s, %(receiver)s', {'sms_code': sms_code, 'receiver': receiver})
                        sent_receivers.add(receiver)

        return sent_receivers, need_retry_receivers

    def send_voice(self, receiver, code, sms_code):
        config = yuntongxun_sms_client_config()
        LOGGER.debug('attempt to send voice: %(sms_code)s, %(receiver)s, %(code)s', {'sms_code': sms_code, 'receiver': receiver, 'code': code})
        data = {'appId': config.app_id, 'verifyCode': code, 'to': receiver, 'playTimes': '2'}
        response = None
        try:
            response = requests.post(SEND_VOICE_URL_TPL.format(config.account_sid), headers=generate_request_headers(), params={'sig': generate_sig()},
                                     json=data, timeout=(3.05, 9),
                                     max_retries=Retry(total=2, read=False, method_whitelist={'POST'}, status_forcelist={502, 503, 504}, backoff_factor=2))
            response.raise_for_status()
        except ReadTimeout:
                LOGGER.exception('yuntongxun send voice validation code got ReadTimeout exception: %(sms_code)s, %(receiver)s',
                                 {'sms_code': sms_code, 'receiver': receiver})
                raise
        except Exception as e:
            LOGGER.exception('yuntongxun send voice validation code got exception-thrown: %(sms_code)s, %(receiver)s, %(message)s, %(response)s', {
                'sms_code': sms_code, 'receiver': receiver, 'message': e.message, 'response': response.text if response else ''
            })
            raise
        else:
            try:
                result = objectify(response.json())
            except Exception:
                LOGGER.error('yuntongxun query balance got bad format response: %(response)s', {'response': response.text})
                raise
            else:
                if result.statusCode != REQUEST_SUCCESS_MARK:
                    LOGGER.error('yuntongxun voice send failed: %(sms_code)s, %(response)s, %(receiver)s', {
                        'sms_code': sms_code, 'response': response.text, 'receiver': receiver
                    })
                    raise SendError('yuntongxun sms send failed: {}, {}'.format(sms_code, receiver), receiver)
                else:
                    LOGGER.info('yuntongxun voice send succeeded: %(sms_code)s, %(receiver)s', {'sms_code': sms_code, 'receiver': receiver})

    def query_balance(self):
        config = yuntongxun_sms_client_config()
        response = None
        try:
            response = requests.get(QUERY_BALANCE_URL_TPL.format(config.account_sid), headers=generate_request_headers(),
                                    params={'sig': generate_sig()}, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
            response.raise_for_status()
        except Exception:
            LOGGER.exception('yuntongxun query balance exception-thrown: %(response)s', {'response': response.text if response else ''})
            raise
        else:
            LOGGER.debug(response.content)
            try:
                result = objectify(response.json())
            except Exception:
                LOGGER.error('yuntongxun query balance got bad format response: %(response)s', {'response': response.text})
                raise
            else:
                if result.statusCode != REQUEST_SUCCESS_MARK:
                    LOGGER.error('yuntongxun query balance got failed response: %(response)s', {'response': response.text})
                    raise Exception('yuntongxun query balance got failed response')
                balance = int(result.Account.balance)
            return balance

    def get_minimal_message_quantity(self, message):
        return 1
