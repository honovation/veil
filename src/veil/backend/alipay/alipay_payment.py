# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
from veil.environment import *
from veil.utility.encoding import *
from veil.utility.http import *
from veil.model.binding import *
from veil.model.event import *
from veil.profile.web import *
from .alipay_client_installer import alipay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_ALIPAY_TRADE_PAID = define_event('alipay-trade-paid') # valid notification

PAYMENT_URL_TEMPLATE = 'https://mapi.alipay.com/gateway.do?{}'
VERIFY_URL_TEMPLATE = 'https://mapi.alipay.com/gateway.do?service=notify_verify&partner={}&notify_id={}'

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success' # alipay require this 7 characters to be returned to them


def create_alipay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, minutes_to_complete_payment,
        shopper_ip_address):
    params = {
        'service': 'create_direct_pay_by_user', #即时到帐
        'partner': alipay_client_config().partner_id,
        '_input_charset': 'UTF-8',
        'out_trade_no': out_trade_no,
        'subject': subject,
        'payment_type': '1',
        'seller_email': alipay_client_config().seller_email,
        'total_fee': '%.2f' % total_fee,
        'body': body,
        'show_url': show_url,
        'return_url': return_url,
        'notify_url': notify_url,
        # paymethod=directPay
        # paymethod=motoPay
        # paymethod=bankPay, defaultbank=CMB
        # paymethod=expressGateway, default_login=Y
        'paymethod': 'directPay',
        'exter_invoke_ip': shopper_ip_address, # 防钓鱼IP地址检查 (支付宝端设置已取消，这是我们期望的)
        'extra_common_param': show_url,
        'it_b_pay': '{}m'.format(minutes_to_complete_payment), # 未付款交易的超时时间
        # TODO: default_login 自动登录
        # TODO: token 快捷登录授权令牌
    }
    sign = sign_md5(params)
    params['sign'] = sign
    params['sign_type'] = 'MD5'
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    return PAYMENT_URL_TEMPLATE.format(urllib.urlencode(params))


def process_alipay_payment_notification(out_trade_no, http_arguments, notified_from):
    trade_no, buyer_id, paid_total, paid_at, show_url, discarded_reasons = validate_notification(http_arguments)
    if discarded_reasons:
        LOGGER.warn('alipay trade notification discarded: %(discarded_reasons)s, %(http_arguments)s', {
            'discarded_reasons': discarded_reasons,
            'http_arguments': http_arguments
        })
        set_http_status_code(httplib.BAD_REQUEST)
        return '<br/>'.join(discarded_reasons)
    publish_event(EVENT_ALIPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
        paid_total=paid_total, paid_at=paid_at, show_url=show_url, notified_from=notified_from)
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
                if not is_notification_from_alipay(notify_id):
                    discarded_reasons.append('notification not from alipay')
            else:
                discarded_reasons.append('no notify_id')
        else:
            discarded_reasons.append('sign is incorrect')
    if http_arguments.get('trade_status', None) not in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
        discarded_reasons.append('trade not succeeded')
    if not http_arguments.get('out_trade_no', None):
        discarded_reasons.append('no out_trade_no')
    trade_no = http_arguments.get('trade_no', None)
    if not trade_no:
        discarded_reasons.append('no trade_no')
    if alipay_client_config().seller_email != http_arguments.get('seller_email', None):
        discarded_reasons.append('seller email mismatched')
    paid_total = http_arguments.get('total_fee', None)
    if paid_total:
        try:
            paid_total = Decimal(paid_total)
        except DecimalException:
            LOGGER.warn('invalid total_fee: %(total_fee)s', {'total_fee': paid_total})
            discarded_reasons.append('invalid total_fee')
    else:
        discarded_reasons.append('no total_fee')
    paid_at = http_arguments.get('gmt_payment', None) or http_arguments.get('notify_time', None) # 买家付款时间，时区为GMT+8 beijing，格式为 yyyy-MM-dd HH:mm:ss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y-%m-%d %H:%M:%S')(paid_at)
        except Exception:
            LOGGER.warn('invalid gmt_payment or notify_time: %(paid_at)s', {'paid_at': paid_at})
            discarded_reasons.append('invalid gmt_payment or notify_time')
    else:
        discarded_reasons.append('no gmt_payment or notify_time')
    show_url = http_arguments.get('extra_common_param', None)
    if not show_url:
        discarded_reasons.append('no extra_common_param (show_url inside)')
    return trade_no, http_arguments.get('buyer_id', None), paid_total, paid_at, show_url, discarded_reasons


def is_sign_correct(http_arguments):
    actual_sign = http_arguments.get('sign', None)
    verify_params = http_arguments.copy()
    if 'sign' in verify_params:
        del verify_params['sign']
    if 'sign_type' in verify_params:
        del verify_params['sign_type']
    expected_sign = sign_md5(verify_params)
    if actual_sign != expected_sign:
        LOGGER.error('wrong sign, maybe a fake alipay notification: sign=%(actual_sign)s, should be %(expected_sign)s, http_arguments: %(http_arguments)s', {
            'actual_sign': actual_sign,
            'expected_sign': expected_sign,
            'http_arguments': http_arguments
        })
        return False
    return True


def sign_md5(params):
    param_str = '{}{}'.format(to_url_params_string(params), alipay_client_config().app_key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest()


def to_url_params_string(params):
    keys = params.keys()
    keys.sort()
    return '&'.join('{}={}'.format(key, params[key]) for key in keys if params[key])


def is_notification_from_alipay(notify_id):
    verify_url = VERIFY_URL_TEMPLATE.format(alipay_client_config().partner_id, notify_id)
    try:
        response = http_call('ALIPAY-NOTIFY-VERIFY-API', verify_url, max_tries=2)
    except Exception as e:
        response = None
    if 'true' == response:
        LOGGER.debug('alipay notify verify passed: %(response)s, %(verify_url)s', {'response': response, 'verify_url': verify_url})
        return True
    LOGGER.error('received notification not from alipay: %(response)s, %(verify_url)s', {
        'response': response, 'verify_url': verify_url
    })
    return False