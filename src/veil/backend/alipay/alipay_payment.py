# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
import lxml.objectify
from veil.environment import VEIL_ENV_TYPE
from veil.utility.http import *
from veil.utility.encoding import *
from veil.frontend.cli import *
from veil.profile.model import *
from veil.profile.web import *
from .alipay_client_installer import alipay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_ALIPAY_TRADE_PAID = define_event('alipay-trade-paid')  # valid notification

PAYMENT_URL = 'https://mapi.alipay.com/gateway.do'
VERIFY_URL = PAYMENT_URL

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFIED_FROM_PAYMENT_QUERY = 'payment_query'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success'  # alipay require this 7 characters to be returned to them


def create_alipay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, minutes_to_complete_payment,
        shopper_ip_address):
    params = {
        'service': 'create_direct_pay_by_user',  #即时到帐
        'partner': alipay_client_config().partner_id,
        '_input_charset': 'UTF-8',
        'out_trade_no': out_trade_no,
        'subject': subject,
        'payment_type': '1',
        'seller_email': alipay_client_config().seller_email,
        'total_fee': '{:.2f}'.format(total_fee),
        'body': body,
        'show_url': show_url,
        'return_url': return_url,
        'notify_url': notify_url,
        'paymethod': 'directPay',
        'exter_invoke_ip': shopper_ip_address,  # 防钓鱼IP地址检查 (支付宝端设置已取消，这是我们期望的)
        'extra_common_param': show_url,
        'it_b_pay': '{}m'.format(minutes_to_complete_payment),  # 未付款交易的超时时间
    }
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    query = urllib.urlencode(params)
    return '{}?{}'.format(PAYMENT_URL, query)


@script('query-status')
def query_status(out_trade_no):
    query_alipay_payment_status(out_trade_no)


def query_alipay_payment_status(out_trade_no):
    params = {'service': 'single_trade_query', 'partner': alipay_client_config().partner_id, '_input_charset': 'UTF-8', 'out_trade_no': out_trade_no}
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    try:
        response = requests.get(PAYMENT_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('alipay payment query exception-thrown: %(params)s', {'params': params})
        raise
    else:
        arguments = parse_payment_status_response(response.content)
        discarded_reasons = process_alipay_payment_notification(out_trade_no, arguments, NOTIFIED_FROM_PAYMENT_QUERY)
        paid = not bool(discarded_reasons)
    return paid


def parse_payment_status_response(response):
    root = lxml.objectify.fromstring(response)
    arguments = DictObject(sign=root.sign.text, sign_type=root.sign_type.text)
    if arguments.is_success.text == 'T':
        for e in root.response.trade.iterchildren():
            if e.text:
                arguments[e.tag] = e.text
    else:
        arguments.error = root.error.text
    return arguments


def process_alipay_payment_notification(out_trade_no, arguments, notified_from):
    trade_no, buyer_id, paid_total, paid_at, show_url, discarded_reasons = validate_payment_notification(out_trade_no, arguments,
        NOTIFIED_FROM_PAYMENT_QUERY != notified_from)
    if discarded_reasons:
        LOGGER.warn('alipay trade notification discarded: %(discarded_reasons)s, %(arguments)s', {
            'discarded_reasons': discarded_reasons,
            'arguments': arguments
        })
        if NOTIFIED_FROM_PAYMENT_QUERY == notified_from:
            return discarded_reasons
        else:
            set_http_status_code(httplib.BAD_REQUEST)
            return '<br/>'.join(discarded_reasons)
    publish_event(EVENT_ALIPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
        paid_total=paid_total, paid_at=paid_at, show_url=show_url, notified_from=notified_from)
    if NOTIFIED_FROM_RETURN_URL == notified_from:
        redirect_to(show_url or '/')
    elif NOTIFIED_FROM_NOTIFY_URL == notified_from:
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
                    error = validate_notification_from_alipay(notify_id)
                    if error:
                        discarded_reasons.append(error)
                else:
                    discarded_reasons.append('no notify_id')
        else:
            discarded_reasons.append('sign is incorrect')

    error = arguments.get('error')  # payment query failure response
    if error:
        discarded_reasons.append('error: {}'.format(error))
        return None, None, None, None, None, discarded_reasons

    if arguments.get('trade_status') not in {'TRADE_SUCCESS', 'TRADE_FINISHED'}:
        discarded_reasons.append('trade not succeeded')
    out_trade_no_ = arguments.get('out_trade_no')
    if not out_trade_no_:
        discarded_reasons.append('no out_trade_no')
    elif out_trade_no_ != out_trade_no:
        discarded_reasons.append('inconsistent out_trade_no: expected={}, actual={}'.format(out_trade_no, out_trade_no_))
    trade_no = arguments.get('trade_no')
    if not trade_no:
        discarded_reasons.append('no trade_no')
    if alipay_client_config().seller_email != arguments.get('seller_email'):
        discarded_reasons.append('seller email mismatched')
    paid_total = arguments.get('total_fee')
    if paid_total:
        try:
            paid_total = Decimal(paid_total)
        except DecimalException:
            discarded_reasons.append('invalid total_fee: {}'.format(paid_total))
    else:
        discarded_reasons.append('no total_fee')
    paid_at = arguments.get('gmt_payment') or arguments.get('notify_time')  # 买家付款时间，时区为GMT+8 beijing，格式为 yyyy-MM-dd HH:mm:ss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y-%m-%d %H:%M:%S')(paid_at)
        except:
            discarded_reasons.append('invalid gmt_payment or notify_time: {}'.format(paid_at))
    else:
        discarded_reasons.append('no gmt_payment or notify_time')
    show_url = arguments.get('extra_common_param')
    return trade_no, arguments.get('buyer_id'), paid_total, paid_at, show_url, discarded_reasons


def is_sign_correct(arguments):
    actual_sign = arguments.get('sign')
    verify_params = arguments.copy()
    verify_params.pop('sign', None)
    verify_params.pop('sign_type', None)
    expected_sign = sign_md5(verify_params)
    if actual_sign != expected_sign:
        LOGGER.error('wrong sign, maybe a fake alipay notification: sign=%(actual_sign)s, should be %(expected_sign)s, arguments: %(arguments)s', {
            'actual_sign': actual_sign,
            'expected_sign': expected_sign,
            'arguments': arguments
        })
        return False
    return True


def sign_md5(params):
    param_str = '{}{}'.format(to_url_params_string(params), alipay_client_config().app_key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest()


def to_url_params_string(params):
    return '&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key])


def validate_notification_from_alipay(notify_id):
    error = None
    params = {'service': 'notify_verify', 'partner': alipay_client_config().partner_id, 'notify_id': notify_id}
    try:
        response = requests.get(VERIFY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('alipay notify verify exception-thrown: %(params)s', {'params': params})
        error = 'failed to validate alipay notification'
    else:
        if 'true' == response.text:
            LOGGER.debug('alipay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
        else:
            LOGGER.warn('alipay notify verify failed: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
            error = 'notification not from alipay'
    return error
