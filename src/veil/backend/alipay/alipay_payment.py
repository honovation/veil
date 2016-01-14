# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import base64
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
import lxml.objectify
import rsa
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


def make_alipay_order_str(out_trade_no, subject, body, total_fee, notify_url, minutes_to_expire):
    config = alipay_client_config()
    arguments = [('partner', config.partner_id), ('seller_id', config.seller_email), ('out_trade_no', out_trade_no), ('subject', subject), ('body', body),
                 ('total_fee', '{:.2f}'.format(total_fee)), ('notify_url', notify_url), ('service', 'mobile.securitypay.pay'), ('payment_type', '1'),
                 ('_input_charset', 'utf-8'), ('it_b_pay', '{}m'.format(minutes_to_expire))]
    message = '&'.join(['{}="{}"'.format(k, v) for arg in arguments for k, v in [arg]])

    sign = sign_rsa(message, config.rsa_private_key)
    message = '{}&sign="{}"&sign_type="RSA"'.format(message, sign)
    return message


def verify_alipay_sync_notification(message):
    argument_parts = [e.replace('"', '') for e in message.split('"&')]
    sign = None
    arguments = []
    for part in argument_parts:
        if part.startswith('sign'):
            sign = part.split('=')[1]
        elif part.startswith('sign_type'):
            continue
        else:
            arguments.append(tuple(part.split('=')))
    message_ = '&'.join(['{}="{}"'.format(k, v) for arg in arguments for k, v in [arg]])
    config = alipay_client_config()
    try:
        verify_rsa(message_.encode('UTF-8'), base64.b64decode(sign), config.alipay_public_key)
    except:
        return False
    else:
        return True


def create_alipay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, minutes_to_expire, shopper_ip_address):
    params = dict(service='create_direct_pay_by_user', partner=alipay_client_config().partner_id, _input_charset='UTF-8', out_trade_no=out_trade_no,
                  subject=subject, payment_type='1', seller_email=alipay_client_config().seller_email, total_fee='{:.2f}'.format(total_fee), body=body,
                  show_url=show_url, return_url=return_url, notify_url=notify_url, paymethod='directPay', exter_invoke_ip=shopper_ip_address,
                  extra_common_param=show_url, it_b_pay='{}m'.format(minutes_to_expire))
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    try:
        query = urllib.urlencode(params)
    except UnicodeDecodeError as e:
        LOGGER.info('generate alipay payment url got unicode decode error: %(params)s, %(message)s', {
            'params': params,
            'message': e.message
        })
        query = urllib.urlencode(params)
    return '{}?{}'.format(PAYMENT_URL, query)


@script('query-status')
def query_status(out_trade_no):
    query_alipay_payment_status(out_trade_no)


def query_alipay_payment_status(out_trade_no):
    params = dict(service='single_trade_query', partner=alipay_client_config().partner_id, _input_charset='UTF-8', out_trade_no=out_trade_no)
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    try:
        response = requests.get(PAYMENT_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('alipay payment query exception-thrown: %(params)s', {'params': params})
        raise
    else:
        arguments = parse_payment_status_response(response.content)
        if arguments.is_success == 'T':
            arguments.trade.update(sign=arguments.sign, sign_type=arguments.sign_type)
            discarded_reasons = process_alipay_payment_notification(out_trade_no, arguments.trade, NOTIFIED_FROM_PAYMENT_QUERY)
            paid = not bool(discarded_reasons)
        else:
            LOGGER.warn('alipay payment query failed: %(params)s, %(arguments)s', {'params': params, 'arguments': arguments})
            paid = False
    return paid


def parse_payment_status_response(response):
    arguments = DictObject(trade=DictObject())
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    if arguments.is_success == 'T':
        for e in root.response.trade.iterchildren():
            if e.text:
                arguments.trade[e.tag] = e.text
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
        verify_sign_func = is_sign_correct if arguments.sign_type == 'MD5' else is_rsa_sign_correct
        if verify_sign_func(arguments):
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
        except Exception:
            discarded_reasons.append('invalid gmt_payment or notify_time: {}'.format(paid_at))
    else:
        discarded_reasons.append('no gmt_payment or notify_time')
    show_url = arguments.get('extra_common_param')
    return trade_no, arguments.get('buyer_id'), paid_total, paid_at, show_url, discarded_reasons


def is_rsa_sign_correct(arguments):
    config = alipay_client_config()
    actual_sign = arguments.get('sign')
    verify_params = arguments.copy()
    verify_params.pop('sign', None)
    verify_params.pop('sign_type', None)
    try:
        verify_rsa(to_url_params_string(verify_params).encode('UTF-8'), base64.b64decode(actual_sign), config.alipay_public_key)
    except:
        return False
    else:
        return True


def verify_rsa(message, sign, public_key_path):
    with open(public_key_path) as f:
        public_key = rsa.PublicKey.load_pkcs1_openssl_pem(f.read())
    try:
        rsa.verify(message, sign, public_key)
    except rsa.VerificationError:
        raise Exception('verify failed')


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


def sign_rsa(message, keyfile_path):
    with open(keyfile_path) as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())
    return urllib.quote(base64.b64encode(rsa.sign(message.encode('UTF-8'), private_key, 'SHA-1')))


def to_url_params_string(params):
    return '&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key])


def validate_notification_from_alipay(notify_id):
    error = None
    params = {'service': 'notify_verify', 'partner': alipay_client_config().partner_id, 'notify_id': notify_id}
    try:
        response = requests.get(VERIFY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('alipay notify verify exception-thrown: %(params)s', {'params': params})
        error = 'failed to validate alipay notification'
    else:
        if 'true' == response.text:
            LOGGER.debug('alipay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
        else:
            LOGGER.warn('alipay notify verify failed: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
            error = 'notification not from alipay'
    return error


@script('close-trade')
def close_alipay_trade_script(out_trade_no):
    close_alipay_trade(out_trade_no)


def close_alipay_trade(out_trade_no):
    params = dict(service='close_trade', partner=alipay_client_config().partner_id, _input_charset='UTF-8', out_order_no=out_trade_no, trade_role='S')
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    response = None
    try:
        response = requests.get(PAYMENT_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('alipay close trade exception-thrown: %(params)s, %(response)s', {
            'params': params,
            'response': response.text if response else ''
        })
        raise
    else:
        arguments = lxml.objectify.fromstring(response.content)
        if arguments.is_success == 'T':
            LOGGER.info('alipay trade closed: %(out_trade_no)s, %(response)s', {
                'out_trade_no': out_trade_no,
                'response': response.text
            })
        else:
            LOGGER.warn('alipay trade close failed: %(out_trade_no)s, %(params)s, %(error)s', {
                'out_trade_no': out_trade_no,
                'params': params,
                'error': arguments.error
            })
