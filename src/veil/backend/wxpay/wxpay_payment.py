# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from decimal import Decimal, DecimalException
import logging
import urllib
import hashlib
from uuid import uuid4
import lxml.objectify
from veil.environment import VEIL_ENV_TYPE
from veil.frontend.cli import *
from veil.backend.redis import *
from veil.utility.clock import *
from veil.model.binding import *
from veil.model.event import *
from veil.model.collection import *
from veil.profile.web import *
from veil.utility.http import *
from veil.utility.encoding import *
from .wxpay_client_installer import wxpay_client_config

LOGGER = logging.getLogger(__name__)
redis = register_redis('persist_store')

EVENT_WXPAY_TRADE_PAID = define_event('wxpay-trade-paid')  # valid notification
EVENT_WXPAY_DELIVER_NOTIFY_SENT = define_event('wxpay-deliver-notify-sent')

WXMP_ACCESS_TOKEN_KEY = 'wxmp-access-token'

NOTIFIED_FROM_ORDER_QUERY = 'order_query'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success'  # wxpay require this 7 characters to be returned to them
WXPAY_BANK_TYPE = 'WX'
WXPAY_ORDER_QUERY_URL = 'https://api.weixin.qq.com/pay/orderquery'
WXPAY_DELIVER_NOTIFY_URL = 'https://api.weixin.qq.com/pay/delivernotify'
WXMP_ACCESS_TOKEN_AUTHORIZATION_URL = 'https://api.weixin.qq.com/cgi-bin/token'
VERIFY_URL = 'https://gw.tenpay.com/gateway/simpleverifynotifyid.xml'


def get_wxmp_access_token(with_ttl=False, access_token_to_refresh=None):
    if VEIL_ENV_TYPE not in {'public', 'staging'}:
        raise Exception('cannot get wx access token under environment: {}'.format(VEIL_ENV_TYPE))
    if not access_token_to_refresh:
        with redis().pipeline() as pipe:
            pipe.get(WXMP_ACCESS_TOKEN_KEY)
            pipe.ttl(WXMP_ACCESS_TOKEN_KEY)
            access_token, ttl = pipe.execute()
    if access_token_to_refresh or not access_token or ttl <= 0:
        access_token, ttl = refresh_wxmp_access_token(access_token_to_refresh or access_token)
    return DictObject(access_token=access_token, expires_in=ttl) if with_ttl else access_token


@script('refresh-access-token')
def refresh_wxmp_access_token_(access_token_to_refresh=None):
    access_token, ttl = refresh_wxmp_access_token(access_token_to_refresh)
    LOGGER.info('wxmp access token refreshed: %(access_token)s, %(ttl)s, %(access_token_to_refresh)s', {
        'access_token': access_token, 'ttl': ttl, 'access_token_to_refresh': access_token_to_refresh
    })


def refresh_wxmp_access_token(access_token_to_refresh):
    with redis().lock('lock:refresh-wxmp-access-token', timeout=2 * 60):
        with redis().pipeline() as pipe:
            pipe.get(WXMP_ACCESS_TOKEN_KEY)
            pipe.ttl(WXMP_ACCESS_TOKEN_KEY)
            access_token, ttl = pipe.execute()
        if not access_token or ttl <= 0 or access_token == access_token_to_refresh:
            access_token, expires_in = request_wxmp_access_token()
            ttl = expires_in - 300
            redis().setex(WXMP_ACCESS_TOKEN_KEY, ttl, access_token)
    return access_token, ttl


def request_wxmp_access_token():
    config = wxpay_client_config()
    params = dict(grant_type='client_credential', appid=config.app_id, secret=config.app_secret)
    try:
        response = requests.get(WXMP_ACCESS_TOKEN_AUTHORIZATION_URL, params=params, headers={'Accept': 'application/json'}, timeout=(3.05, 9),
            max_retries=Retry(total=5, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('wxmp request access token exception-thrown')
        raise
    else:
        result = objectify(response.json())
        if hasattr(result, 'access_token'):
            LOGGER.info('wxmp request access token succeeded: %(result)s, %(appid)s', {'result': result, 'appid': params['appid']})
            return result.access_token, result.expires_in
        else:
            LOGGER.error('wxmp request access token failed: %(result)s', {'result': result})
            raise Exception('wxmp request access token failed: {}'.format(result))


def create_wxpay_package(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address):
    time_start_beijing_time_str = convert_datetime_to_client_timezone(time_start).strftime('%Y%m%d%H%M%S')
    time_expire_beijing_time_str = convert_datetime_to_client_timezone(time_expire).strftime('%Y%m%d%H%M%S')
    params = {
        'bank_type': WXPAY_BANK_TYPE,
        'body': body,
        'attach': show_url,
        'partner': wxpay_client_config().partner_id,
        'out_trade_no': out_trade_no,
        'total_fee': unicode(int(total_fee * 100)),  # unit: cent
        'fee_type': '1',
        'notify_url': notify_url,
        'spbill_create_ip': shopper_ip_address,  # 防钓鱼IP地址检查
        'time_start': time_start_beijing_time_str,  # 交易起始时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'time_expire': time_expire_beijing_time_str,  # 交易结束时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
        'input_charset': 'UTF-8'
    }
    encoded_params = '&'.join('{}={}'.format(key, urllib.quote(to_str(params[key]))) for key in sorted(params) if params[key])
    sign = sign_md5(params)
    return '{}&sign={}'.format(encoded_params, sign)


def decode_wxpay_package(package, need_verify_sign=True):
    package = urllib.unquote(package)
    params = DictObject((to_unicode(k), urllib.unquote(to_unicode(v))) for p in package.split('&') for k, v in [tuple(p.split('='))])
    sign = params.pop('sign')
    if need_verify_sign:
        verify_sign(params, sign)
    return params


def get_wxpay_request(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address):
    request = DictObject()
    config = wxpay_client_config()
    request.appId = config.app_id
    request.timeStamp = unicode(get_current_timestamp())
    request.nonceStr = uuid4().get_hex()
    request.package = create_wxpay_package(out_trade_no, body, total_fee, show_url, notify_url, time_start, time_expire, shopper_ip_address)
    request.signType = 'SHA1'
    params = {
        'appid': request.appId,
        'timestamp': request.timeStamp,
        'noncestr': request.nonceStr,
        'package': request.package,
        'appkey': config.pay_sign_key
    }
    request.paySign = sign_sha1(params)
    return request


def sign_sha1(params):
    param_str = to_url_params_string(params)
    return hashlib.sha1(param_str.encode('UTF-8')).hexdigest()


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


def query_order_status(out_trade_no, access_token=None):
    access_token = access_token or get_wxmp_access_token()
    try:
        paid = query_order_status_(access_token, out_trade_no)
    except InvalidWXAccessToken:
        paid = query_order_status_(get_wxmp_access_token(access_token_to_refresh=access_token), out_trade_no)
    return paid


def query_order_status_(access_token, out_trade_no):
    paid = False
    params = dict(access_token=access_token)
    config = wxpay_client_config()
    data = dict(appid=config.app_id, package=create_wxpay_query_order_status_package(out_trade_no), timestamp=unicode(get_current_timestamp()))
    data['app_signature'] = sign_sha1(dict(data, appkey=config.pay_sign_key))
    data['sign_method'] = 'sha1'
    headers = {'Content-Type': 'application/json; charset=UTF-8', 'Accept': 'application/json'}
    try:
        response = requests.post(WXPAY_ORDER_QUERY_URL, params=params, json=data, headers=headers, timeout=(3.05, 9),
            max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('wxpay order query exception-thrown: %(out_trade_no)s, %(data)s', {'out_trade_no': out_trade_no, 'data': data})
        raise
    else:
        result = objectify(response.json())
        if result.errcode == 0 and result.order_info.ret_code == 0 and result.order_info.trade_state == '0':
            LOGGER.debug('wxpay order query succeeded: %(out_trade_no)s, %(result)s', {'out_trade_no': out_trade_no, 'result': result})
            trade_no, paid_total, paid_at, bank_billno, errors = validate_order_info(result.order_info)
            if errors:
                LOGGER.error('wxpay order query invalid order_info found: %(errors)s, %(order_info)s', {
                    'errors': errors,
                    'order_info': result.order_info
                })
            else:
                publish_event(EVENT_WXPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=None,
                    paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=None, bank_billno=bank_billno, show_url=None,
                    notified_from=NOTIFIED_FROM_ORDER_QUERY)
                paid = True
        else:
            if result.errcode in (40001, 40014):
                raise InvalidWXAccessToken('wxpay order query invalid access token: {}, {}'.format(out_trade_no, result))
    return paid


def send_deliver_notify(out_trade_no, openid, transid, deliver_status, deliver_msg, access_token=None):
    access_token = access_token or get_wxmp_access_token()
    try:
        send_deliver_notify_(access_token, out_trade_no, openid, transid, deliver_status, deliver_msg)
    except InvalidWXAccessToken:
        send_deliver_notify_(get_wxmp_access_token(access_token_to_refresh=access_token), out_trade_no, openid, transid, deliver_status, deliver_msg)


def send_deliver_notify_(access_token, out_trade_no, openid, transid, deliver_status, deliver_msg):
    params = dict(access_token=access_token)
    config = wxpay_client_config()
    data = dict(appid=config.app_id, openid=openid, transid=transid, out_trade_no=out_trade_no, deliver_timestamp=unicode(get_current_timestamp()),
        deliver_status=deliver_status, deliver_msg=deliver_msg)
    data['app_signature'] = sign_sha1(dict(data, appkey=config.pay_sign_key))
    data['sign_method'] = 'sha1'
    headers = {'Content-Type': 'application/json; charset=UTF-8', 'Accept': 'application/json'}
    try:
        response = requests.post(WXPAY_DELIVER_NOTIFY_URL, params=params, json=data, headers=headers, timeout=(3.05, 9),
            max_retries=Retry(total=3, read=False, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('wxpay deliver notify exception-thrown: %(out_trade_no)s, %(data)s', {'out_trade_no': out_trade_no, 'data': data})
        raise
    else:
        result = objectify(response.json())
        if result.errcode == 0:
            LOGGER.info('wxpay deliver notify succeeded: %(out_trade_no)s, %(result)s', {'out_trade_no': out_trade_no, 'result': result})
            publish_event(EVENT_WXPAY_DELIVER_NOTIFY_SENT, out_trade_no=out_trade_no)
        else:
            LOGGER.error('wxpay deliver notify failed: %(out_trade_no)s, %(result)s', {'out_trade_no': out_trade_no, 'result': result})
            if result.errcode in (40001, 40014):
                raise InvalidWXAccessToken('wxpay deliver notify invalid access token: {}, {}'.format(out_trade_no, result))
            else:
                raise Exception('wxpay deliver notify failed: {}, {}'.format(out_trade_no, result))


def create_wxpay_query_order_status_package(out_trade_no):
    config = wxpay_client_config()
    params = {
        'out_trade_no': out_trade_no,
        'partner': config.partner_id
    }
    encoded_params = '&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key])
    return '{}&sign={}'.format(encoded_params, sign_md5(DictObject(out_trade_no=out_trade_no, partner=config.partner_id)))


def validate_order_info(order_info):
    errors = []
    trade_no = order_info.transaction_id
    if not trade_no:
        errors.append('no transaction_id')
    paid_total = order_info.total_fee
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            errors.append('invalid total_fee: {}'.format(paid_total))
    paid_at = order_info.time_end
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except:
            errors.append('invalid time_end: {}'.format(paid_at))
    bank_billno = order_info.bank_billno
    return trade_no, paid_total, paid_at, bank_billno, errors


def validate_notification(http_arguments):
    discarded_reasons = []
    if VEIL_ENV_TYPE not in {'development', 'test'}:
        if is_sign_correct(http_arguments):
            notify_id = http_arguments.get('notify_id')
            if notify_id:
                error = validate_notification_from_wxpay(notify_id)
                if error:
                    discarded_reasons.append(error)
            else:
                discarded_reasons.append('no notify_id')
        else:
            discarded_reasons.append('sign is incorrect')
    if '0' != http_arguments.get('trade_state'):
        discarded_reasons.append('trade not succeeded')
    if not http_arguments.get('out_trade_no'):
        discarded_reasons.append('no out_trade_no')
    trade_no = http_arguments.get('transaction_id')
    if not trade_no:
        discarded_reasons.append('no transaction_id')
    if wxpay_client_config().partner_id != http_arguments.get('partner'):
        discarded_reasons.append('partner ID mismatched')
    paid_total = http_arguments.get('total_fee')
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            discarded_reasons.append('invalid total_fee: {}'.format(paid_total))
    else:
        discarded_reasons.append('no total_fee')
    paid_at = http_arguments.get('time_end') # 支付完成时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except:
            discarded_reasons.append('invalid time_end: {}'.format(paid_at))
    else:
        discarded_reasons.append('no time_end')
    show_url = http_arguments.get('attach')
    buyer_alias = http_arguments.get('buyer_alias')
    bank_code = http_arguments.get('bank_type')
    bank_billno = http_arguments.get('bank_billno')
    return trade_no, buyer_alias, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons


def validate_notification_from_wxpay(notify_id):
    error = None
    params = {'sign_type': 'MD5', 'input_charset': 'UTF-8', 'partner': wxpay_client_config().partner_id, 'notify_id': notify_id}
    params['sign'] = sign_md5(params)
    try:
        response = requests.get(VERIFY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except:
        LOGGER.exception('wxpay notify verify exception-thrown: %(params)s', {'params': params})
        error = 'failed to validate wxpay notification'
    else:
        arguments = parse_notify_verify_response(response.content)
        if is_sign_correct(arguments) and '0' == arguments.get('retcode'):
            LOGGER.debug('wxpay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
        else:
            LOGGER.warn('wxpay notify verify failed: %(response)s, %(verify_url)s', {'response': response.text, 'verify_url': response.url})
            error = 'notification not from wxpay'
    return error


def verify_sign(content, sign=None):
    sign = sign or content.pop('sign', None)
    if not sign or sign.upper() != sign_md5(content):
        raise Exception('failed to verify sign: sign={}, content={}'.format(sign, content))


def is_sign_correct(arguments):
    try:
        verify_sign(arguments)
    except:
        LOGGER.exception('wrong sign, maybe a fake wxpay notification')
        return False
    else:
        return True


def sign_md5(params):
    param_str = '{}&key={}'.format(to_url_params_string(params), wxpay_client_config().partner_key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest().upper()


def to_url_params_string(params):
    return '&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key])


def parse_notify_verify_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments


class InvalidWXAccessToken(Exception):
    pass