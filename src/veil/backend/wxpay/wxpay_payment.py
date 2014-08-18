# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
from uuid import uuid4
import lxml.objectify
from veil.environment import VEIL_ENV_TYPE
from veil.utility.clock import *
from veil.model.binding import *
from veil.model.event import *
from veil.model.collection import *
from veil.profile.web import *
from veil.utility.encoding import *
from veil.utility.http import *
from veil.utility.json import *
from .wxpay_client_installer import wxpay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_WXPAY_TRADE_PAID = define_event('wxpay-trade-paid') # valid notification
EVENT_WXPAY_DELIVER_NOTIFY_SENT = define_event('wxpay-deliver-notify-sent')


NOTIFIED_FROM_ORDER_QUERY = 'order_query'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success' # wxpay require this 7 characters to be returned to them
WXPAY_BANK_TYPE = 'WX'
WXPAY_ORDER_QUERY_URL_TEMPLATE = 'https://api.weixin.qq.com/pay/orderquery?access_token={}'
WXPAY_DELIVER_NOTIFY_URL_TEMPLATE = 'https://api.weixin.qq.com/pay/delivernotify?access_token={}'
WXMP_ACCESS_TOKEN_AUTHORIZATION_URL_TEMPLATE = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'
VERIFY_URL_TEMPLATE = 'https://gw.tenpay.com/gateway/simpleverifynotifyid.xml?{}'


def create_wxpay_package(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address):
    time_start_beijing_time_str = convert_datetime_to_client_timezone(time_start).strftime('%Y%m%d%H%M%S')
    time_expire_beijing_time_str = convert_datetime_to_client_timezone(time_expire).strftime('%Y%m%d%H%M%S')
    params = {
        'bank_type': WXPAY_BANK_TYPE,
        'body': body,
        'attach': show_url,
        'partner': wxpay_client_config().partner_id,
        'out_trade_no': out_trade_no,
        'total_fee': str(int(total_fee * 100)), # unit: cent
        'fee_type': '1',
        'notify_url': notify_url,
        'spbill_create_ip': shopper_ip_address, # 防钓鱼IP地址检查
        'time_start': time_start_beijing_time_str, # 交易起始时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'time_expire': time_expire_beijing_time_str, # 交易结束时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'input_charset': 'UTF-8'
    }
    encoded_params = '&'.join('{}={}'.format(to_str(key), urllib.quote(to_str(params[key]))) for key in sorted(params.keys()) if params[key])
    sign = sign_md5(params)
    return '{}&sign={}'.format(encoded_params, sign)


def get_wxpay_request(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address):
    request = DictObject()
    request.appId = wxpay_client_config().app_id
    request.timeStamp = str(get_current_timestamp())
    request.nonceStr = uuid4().get_hex()
    request.package = create_wxpay_package(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address)
    request.signType = 'SHA1'
    params = {
        'appid': request.appId,
        'timestamp': request.timeStamp,
        'noncestr': request.nonceStr,
        'package': request.package,
        'appkey': wxpay_client_config().pay_sign_key
    }
    params = {to_str(k): to_str(v) for k, v in params.items()}
    request.paySign = sign_sha1(params)
    return request


def sign_sha1(params):
    param_str = to_url_params_string(params)
    return hashlib.sha1(param_str).hexdigest()


def process_wxpay_payment_notification(out_trade_no, http_arguments, notified_from):
    trade_no, buyer_id, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons = validate_notification(http_arguments)
    if discarded_reasons:
        LOGGER.warn('wxpay trade notification discarded: %(discarded_reasons)s, %(http_arguments)s', {
            'discarded_reasons': discarded_reasons,
            'http_arguments': http_arguments
        })
        set_http_status_code(httplib.BAD_REQUEST)
        return '<br/>'.join(discarded_reasons)
    publish_event(EVENT_WXPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
        paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=bank_code, bank_billno=bank_billno, show_url=show_url,
        notified_from=notified_from)
    return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


def query_order_status(access_token, out_trade_no):
    params = DictObject()
    params.appid = wxpay_client_config().app_id
    params.package = create_wxpay_query_order_status_package(out_trade_no)
    params.timestamp = str(get_current_timestamp())
    params.app_signature = sign_sha1({
        'appid': params.appid,
        'appkey': wxpay_client_config().pay_sign_key,
        'package': params.package,
        'timestamp': params.timestamp
    })
    params.sign_method = 'sha1'
    try:
        response = http_call('wxpay-order-query', WXPAY_ORDER_QUERY_URL_TEMPLATE.format(access_token), data=params, content_type='application/json', max_tries=3)
    except:
        raise
    else:
        query_result = objectify(from_json(response))
        if query_result.errcode != 0:
            LOGGER.info('Got error from query order status: %(error_message)s, %(response)s', {
                'error_message': query_result.errmsg, 'response': query_result
            })
        else:
            trade_no, paid_total, paid_at, bank_billno = validate_order_info(query_result.order_info)
            publish_event(EVENT_WXPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=None,
                paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=None, bank_billno=bank_billno, show_url=None,
                notified_from=NOTIFIED_FROM_ORDER_QUERY)


def send_deliver_notify(access_token, out_trade_no, openid, transid, deliver_status, deliver_msg):
    params = DictObject()
    params.appid = wxpay_client_config().app_id
    params.openid = openid
    params.transid = transid
    params.out_trade_no = out_trade_no
    params.deliver_timestamp = str(get_current_timestamp())
    params.deliver_status = deliver_status
    params.deliver_msg = deliver_msg
    params.app_signature = sign_sha1({
        'appid': params.appid,
        'appkey': wxpay_client_config().pay_sign_key,
        'openid': params.openid,
        'transid': params.transid,
        'out_trade_no': params.out_trade_no,
        'deliver_timestamp': params.deliver_timestamp,
        'deliver_status': params.deliver_status,
        'deliver_msg': params.deliver_msg
    })
    params.sign_method = 'sha1'
    try:
        response = http_call('wxpay-deliver-notify', WXPAY_DELIVER_NOTIFY_URL_TEMPLATE.format(access_token), data=params, content_type='application/json', max_tries=3)
    except:
        raise
    else:
        query_result = objectify(from_json(response))
        if query_result.errcode != 0:
            LOGGER.info('Got error from send deliver notify: %(error_message)s, %(response)s', {
                'error_message': query_result.errmsg, 'response': query_result
            })
        else:
            publish_event(EVENT_WXPAY_DELIVER_NOTIFY_SENT, out_trade_no=out_trade_no)


def create_wxpay_query_order_status_package(out_trade_no):
    params = {
        'out_trade_no': out_trade_no,
        'partner': wxpay_client_config().partner_id
    }
    encoded_params = '&'.join('{}={}'.format(to_str(key), to_str(params[key])) for key in sorted(params.keys()) if params[key])
    return '{}&sign={}'.format(encoded_params, sign_md5(DictObject(out_trade_no=out_trade_no, partner=wxpay_client_config().partner_id)))


def validate_order_info(order_info):
    trade_no = order_info.transaction_id
    if not trade_no:
        raise OrderInfoException('no transaction id')
    paid_total = order_info.total_fee
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            LOGGER.warn('invalid total_fee: %(total_fee)s', {'total_fee': paid_total})
            raise OrderInfoException('invalid total fee: {}'.format(paid_total))
    paid_at = order_info.time_end
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except Exception:
            LOGGER.warn('invalid time_end: %(paid_at)s', {'paid_at': paid_at})
            raise OrderInfoException('invalid time end format: {}'.format(paid_at))
    bank_billno = order_info.bank_billno

    return trade_no, paid_total, paid_at, bank_billno


def request_wxmp_access_token():
    app_id = wxpay_client_config().app_id
    app_secret = wxpay_client_config().app_secret
    try:
        response = http_call('get-wxmp-access-token', WXMP_ACCESS_TOKEN_AUTHORIZATION_URL_TEMPLATE.format(app_id, app_secret), max_tries=3)
    except:
        raise
    else:
        LOGGER.info('Authorized got access token from wxmp: %(response)s', {'response': response})
        result = objectify(from_json(response))
        return result.access_token


def validate_notification(http_arguments):
    discarded_reasons = []
    if VEIL_ENV_TYPE not in ('development', 'test'):
        if is_sign_correct(http_arguments):
            notify_id = http_arguments.get('notify_id', None)
            if not notify_id:
                discarded_reasons.append('no notify_id')
            if not try_to_verify_notification_is_from_wxpay(notify_id):
                pass
            else:
                LOGGER.info('notification has been verified from wxpay')
        else:
            discarded_reasons.append('sign is incorrect')
    if '0' != http_arguments.get('trade_state', None):
        discarded_reasons.append('trade not succeeded')
    if not http_arguments.get('out_trade_no', None):
        discarded_reasons.append('no out_trade_no')
    trade_no = http_arguments.get('transaction_id', None)
    if not trade_no:
        discarded_reasons.append('no transaction_id')
    if wxpay_client_config().partner_id != http_arguments.get('partner', None):
        discarded_reasons.append('partner ID mismatched')
    paid_total = http_arguments.get('total_fee', None)
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            LOGGER.warn('invalid total_fee: %(total_fee)s', {'total_fee': paid_total})
            discarded_reasons.append('invalid total_fee')
    else:
        discarded_reasons.append('no total_fee')
    paid_at = http_arguments.get('time_end', None) # 支付完成时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except Exception:
            LOGGER.warn('invalid time_end: %(paid_at)s', {'paid_at': paid_at})
            discarded_reasons.append('invalid time_end')
    else:
        discarded_reasons.append('no time_end')
    show_url = http_arguments.get('attach', None)
    if not show_url:
        discarded_reasons.append('no attach (show_url inside)')
    buyer_alias = http_arguments.get('buyer_alias', None)
    bank_code = http_arguments.get('bank_type', None)
    bank_billno = http_arguments.get('bank_billno', None)
    return trade_no, buyer_alias, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons


def try_to_verify_notification_is_from_wxpay(notify_id):
    verify_url = VERIFY_URL_TEMPLATE.format(
        make_query({'sign_type': 'MD5', 'input_charset': 'UTF-8', 'partner': wxpay_client_config().partner_id, 'notify_id': notify_id}))
    try:
        response = http_call('WXPAY-NOTIFY-VERIFY-API', verify_url, max_tries=2)
    except Exception:
        response = None
    if response:
        arguments = parse_notify_verify_response(response)
        if is_sign_correct(arguments) and '0' == arguments.get('retcode', None):
            LOGGER.debug('wxpay notify verify passed: %(response)s, %(verify_url)s', {'response': response, 'verify_url': verify_url})
            return True
    LOGGER.error('received notification not from wxpay: %(response)s, %(verify_url)s', {
        'response': response, 'verify_url': verify_url
    })
    return False


def is_sign_correct(http_arguments):
    actual_sign = http_arguments.get('sign', None)
    verify_params = http_arguments.copy()
    if 'sign' in verify_params:
        del verify_params['sign']
    expected_sign = sign_md5(verify_params)
    if not actual_sign or actual_sign.upper() != expected_sign:
        LOGGER.error('wrong sign, maybe a fake wxpay notification: sign=%(actual_sign)s, should be %(expected_sign)s, http_arguments: %(http_arguments)s', {
            'actual_sign': actual_sign,
            'expected_sign': expected_sign,
            'http_arguments': http_arguments
        })
        return False
    return True


def sign_md5(params):
    param_str = '{}&key={}'.format(to_url_params_string(params), wxpay_client_config().partner_key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest().upper()


def to_url_params_string(params):
    return '&'.join('{}={}'.format(key, params[key]) for key in sorted(params.keys()) if params[key])


def make_query(params):
    if 'sign' in params:
        del params['sign']
    sign = sign_md5(params)
    params['sign'] = sign
    # urllib.urlencode does not handle unicode well
    params = {to_str(k): to_str(v) for k, v in params.items()}
    return urllib.urlencode(params)


def parse_notify_verify_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments


class OrderInfoException(Exception):
    pass