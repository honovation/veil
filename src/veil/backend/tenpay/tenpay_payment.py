# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
import lxml.objectify
import requests
from veil.environment import VEIL_ENV_TYPE
from veil.utility.encoding import *
from veil.utility.clock import *
from veil.model.binding import *
from veil.model.event import *
from veil.model.collection import *
from veil.profile.web import *
from .tenpay_client_installer import tenpay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_TENPAY_TRADE_PAID = define_event('tenpay-trade-paid') # valid notification

PAYMENT_URL = 'https://gw.tenpay.com/gateway/pay.htm'
VERIFY_URL = 'https://gw.tenpay.com/gateway/simpleverifynotifyid.xml'

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success' # tenpay require this 7 characters to be returned to them


def create_tenpay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, time_start, time_expire, shopper_ip_address,
        bank_type):
    bank_type = bank_type or 'DEFAULT'
    time_start_beijing_time_str = convert_datetime_to_client_timezone(time_start).strftime('%Y%m%d%H%M%S')
    time_expire_beijing_time_str = convert_datetime_to_client_timezone(time_expire).strftime('%Y%m%d%H%M%S')
    params = {
        'sign_type': 'MD5',
        'input_charset': 'UTF-8',
        'bank_type': bank_type,
        'body': body,
        'subject': subject,
        'attach': show_url,
        'return_url': return_url,
        'notify_url': notify_url,
        'partner': tenpay_client_config().partner_id,
        'out_trade_no': out_trade_no,
        'total_fee': unicode(int(total_fee * 100)),  # unit: cent
        'fee_type': '1',
        'spbill_create_ip': shopper_ip_address,  # 防钓鱼IP地址检查
        'time_start': time_start_beijing_time_str,  # 交易起始时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'time_expire': time_expire_beijing_time_str,  # 交易结束时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'trade_mode': '1'  # 交易模式：即时到账
    }
    params['sign'] = sign_md5(params)
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    query = urllib.urlencode(params)
    return '{}?{}'.format(PAYMENT_URL, query)


def process_tenpay_payment_notification(out_trade_no, http_arguments, notified_from):
    trade_no, buyer_id, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons = validate_notification(http_arguments)
    if discarded_reasons:
        LOGGER.warn('tenpay trade notification discarded: %(discarded_reasons)s, %(http_arguments)s', {
            'discarded_reasons': discarded_reasons,
            'http_arguments': http_arguments
        })
        set_http_status_code(httplib.BAD_REQUEST)
        return '<br/>'.join(discarded_reasons)
    publish_event(EVENT_TENPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
        paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=bank_code, bank_billno=bank_billno, show_url=show_url,
        notified_from=notified_from)
    if NOTIFIED_FROM_RETURN_URL == notified_from:
        redirect_to(show_url or '/')
    else:
        return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


def validate_notification(http_arguments):
    discarded_reasons = []
    if VEIL_ENV_TYPE not in {'development', 'test'}:
        if is_sign_correct(http_arguments):
            notify_id = http_arguments.get('notify_id', None)
            if notify_id:
                error = validate_notification_from_tenpay(notify_id)
                if error:
                    discarded_reasons.append(error)
            else:
                discarded_reasons.append('no notify_id')
        else:
            discarded_reasons.append('sign is incorrect')
    if '0' != http_arguments.get('trade_state', None):
        discarded_reasons.append('trade not succeeded')
    if not http_arguments.get('out_trade_no', None):
        discarded_reasons.append('no out_trade_no')
    trade_no = http_arguments.get('transaction_id', None)
    if not trade_no:
        discarded_reasons.append('no transaction_id')
    if tenpay_client_config().partner_id != http_arguments.get('partner', None):
        discarded_reasons.append('partner ID mismatched')
    paid_total = http_arguments.get('total_fee', None)
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            discarded_reasons.append('invalid total_fee: {}'.format(paid_total))
    else:
        discarded_reasons.append('no total_fee')
    paid_at = http_arguments.get('time_end', None) # 支付完成时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except:
            discarded_reasons.append('invalid time_end: {}'.format(paid_at))
    else:
        discarded_reasons.append('no time_end')
    show_url = http_arguments.get('attach', None)
    if not show_url:
        discarded_reasons.append('no attach (show_url inside)')
    buyer_alias = http_arguments.get('buyer_alias', None)
    bank_code = http_arguments.get('bank_type', None)
    bank_billno = http_arguments.get('bank_billno', None)
    return trade_no, buyer_alias, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons


def is_sign_correct(http_arguments):
    actual_sign = http_arguments.get('sign', None)
    verify_params = http_arguments.copy()
    if 'sign' in verify_params:
        del verify_params['sign']
    expected_sign = sign_md5(verify_params)
    if not actual_sign or actual_sign.upper() != expected_sign:
        LOGGER.error('wrong sign, maybe a fake tenpay notification: sign=%(actual_sign)s, should be %(expected_sign)s, http_arguments: %(http_arguments)s', {
            'actual_sign': actual_sign,
            'expected_sign': expected_sign,
            'http_arguments': http_arguments
        })
        return False
    return True


def sign_md5(params):
    param_str = '{}&key={}'.format(to_url_params_string(params), tenpay_client_config().app_key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest().upper()


def to_url_params_string(params):
    return '&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key])


def validate_notification_from_tenpay(notify_id):
    error = None
    params = {'sign_type': 'MD5', 'input_charset': 'UTF-8', 'partner': tenpay_client_config().partner_id, 'notify_id': notify_id}
    params['sign'] = sign_md5(params)
    try:
        #TODO: retry when new-version requests supports
        response = requests.get(VERIFY_URL, params=params, timeout=(3.05, 9))
        response.raise_for_status()
    except:
        LOGGER.exception('tenpay notify verify exception-thrown: %(params)s', {'params': params})
        error = 'failed to validate tenpay notification'
    else:
        arguments = parse_notify_verify_response(response.content)
        if is_sign_correct(arguments) and '0' == arguments.get('retcode', None):
            LOGGER.debug('tenpay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
        else:
            LOGGER.warn('tenpay notify verify failed: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
            error = 'notification not from tenpay'
    return error

def parse_notify_verify_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments