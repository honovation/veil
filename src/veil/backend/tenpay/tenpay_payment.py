# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import hashlib
import logging
from decimal import Decimal, DecimalException

import lxml.objectify

from veil.environment import VEIL_ENV_TYPE
from veil.frontend.cli import *
from veil.profile.model import *
from veil.profile.web import *
from .tenpay_client_installer import tenpay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_TENPAY_TRADE_PAID = define_event('tenpay-trade-paid')  # valid notification

PAYMENT_URL = 'https://gw.tenpay.com/gateway/pay.htm'
VERIFY_URL = 'https://gw.tenpay.com/gateway/simpleverifynotifyid.xml'
PAYMENT_QUERY_URL = 'https://gw.tenpay.com/gateway/normalorderquery.xml'

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFIED_FROM_PAYMENT_QUERY = 'payment_query'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success'  # tenpay require this 7 characters to be returned to them


def create_tenpay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, time_start, time_expire, shopper_ip_address, bank_type):
    bank_type = bank_type or 'DEFAULT'
    time_start_beijing_time_str = convert_datetime_to_client_timezone(time_start).strftime('%Y%m%d%H%M%S')
    time_expire_beijing_time_str = convert_datetime_to_client_timezone(time_expire).strftime('%Y%m%d%H%M%S')
    params = dict(sign_type='MD5', input_charset='UTF-8', bank_type=bank_type, body=body, subject=subject, attach=show_url, return_url=return_url,
                  notify_url=notify_url, partner=tenpay_client_config().partner_id, out_trade_no=out_trade_no, total_fee=unicode(int(total_fee * 100)),
                  fee_type='1', spbill_create_ip=shopper_ip_address, time_start=time_start_beijing_time_str, time_expire=time_expire_beijing_time_str,
                  trade_mode='1')
    params['sign'] = sign_md5(params)
    return '{}?{}'.format(PAYMENT_URL, urlencode(params))


@script('query-status')
def query_status(out_trade_no):
    query_tenpay_payment_status(out_trade_no)


def query_tenpay_payment_status(out_trade_no):
    params = {'sign_type': 'MD5', 'input_charset': 'UTF-8', 'partner': tenpay_client_config().partner_id, 'out_trade_no': out_trade_no}
    params['sign'] = sign_md5(params)
    try:
        response = requests.get(PAYMENT_QUERY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('tenpay payment query exception-thrown: %(params)s', {'params': params})
        raise
    else:
        arguments = parse_xml_response(response.content)
        if arguments.retcode == '0':
            discarded_reasons = process_tenpay_payment_notification(out_trade_no, arguments, NOTIFIED_FROM_PAYMENT_QUERY)
            paid = not bool(discarded_reasons)
        else:
            LOGGER.warn('tenpay payment query failed: %(params)s, %(arguments)s', {'params': params, 'arguments': arguments})
            paid = False
    return paid


def process_tenpay_payment_notification(out_trade_no, arguments, notified_from):
    with_notify_id = NOTIFIED_FROM_PAYMENT_QUERY != notified_from
    trade_no, buyer_id, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons = validate_payment_notification(out_trade_no, arguments,
                                                                                                                                 with_notify_id)
    if discarded_reasons:
        LOGGER.warn('tenpay payment notification discarded: %(discarded_reasons)s, %(arguments)s', {
            'discarded_reasons': discarded_reasons,
            'arguments': arguments
        })
    else:
        publish_event(EVENT_TENPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
                      paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=bank_code, bank_billno=bank_billno, show_url=show_url,
                      notified_from=notified_from)
    if NOTIFIED_FROM_RETURN_URL == notified_from:
        return show_url
    elif NOTIFIED_FROM_NOTIFY_URL == notified_from:
        if discarded_reasons:
            set_http_status_code(httplib.BAD_REQUEST)
            return '<br/>'.join(discarded_reasons)
        else:
            return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK
    else:
        return discarded_reasons


def validate_payment_notification(out_trade_no, arguments, with_notify_id=True):
    discarded_reasons = []
    if VEIL_ENV_TYPE not in {'development', 'test'}:
        if is_sign_correct(arguments):
            if with_notify_id:
                notify_id = arguments.get('notify_id')
                if notify_id:
                    error = validate_notification_from_tenpay(notify_id)
                    if error:
                        discarded_reasons.append(error)
                else:
                    discarded_reasons.append('no notify_id')
        else:
            discarded_reasons.append('sign is incorrect')
    if '0' != arguments.get('trade_state'):
        discarded_reasons.append('trade not succeeded')
    out_trade_no_ = arguments.get('out_trade_no')
    if not out_trade_no_:
        discarded_reasons.append('no out_trade_no')
    elif out_trade_no_ != out_trade_no:
        discarded_reasons.append('inconsistent out_trade_no: expected={}, actual={}'.format(out_trade_no, out_trade_no_))
    trade_no = arguments.get('transaction_id')
    if not trade_no:
        discarded_reasons.append('no transaction_id')
    if tenpay_client_config().partner_id != arguments.get('partner'):
        discarded_reasons.append('partner ID mismatched')
    paid_total = arguments.get('total_fee')
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            discarded_reasons.append('invalid total_fee: {}'.format(paid_total))
    else:
        discarded_reasons.append('no total_fee')
    paid_at = arguments.get('time_end') # 支付完成时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except Exception:
            discarded_reasons.append('invalid time_end: {}'.format(paid_at))
    else:
        discarded_reasons.append('no time_end')
    show_url = arguments.get('attach')
    buyer_alias = arguments.get('buyer_alias')
    bank_code = arguments.get('bank_type')
    bank_billno = arguments.get('bank_billno')
    return trade_no, buyer_alias, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons


def is_sign_correct(arguments):
    actual_sign = arguments.get('sign')
    verify_params = arguments.copy()
    verify_params.pop('sign', None)
    expected_sign = sign_md5(verify_params)
    if not actual_sign or actual_sign.upper() != expected_sign:
        LOGGER.error('wrong sign, maybe a fake tenpay notification: sign=%(actual_sign)s, should be %(expected_sign)s, arguments: %(arguments)s', {
            'actual_sign': actual_sign,
            'expected_sign': expected_sign,
            'arguments': arguments
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
        response = requests.get(VERIFY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('tenpay notify verify exception-thrown: %(params)s', {'params': params})
        error = 'failed to validate tenpay notification'
    else:
        arguments = parse_xml_response(response.content)
        if is_sign_correct(arguments) and '0' == arguments.get('retcode'):
            LOGGER.debug('tenpay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
        else:
            LOGGER.warn('tenpay notify verify failed: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
            error = 'notification not from tenpay'
    return error


def parse_xml_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments
