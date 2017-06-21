# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import hashlib
import logging
from decimal import Decimal, DecimalException
from uuid import uuid4

import lxml.objectify

from veil.profile.model import *
from veil.profile.web import *
from .wxpay_client_installer import wxpay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_WXPAY_TRADE_PAID = define_event('wxpay-trade-paid')  # valid notification
EVENT_WXPAY_DELIVER_NOTIFY_SENT = define_event('wxpay-deliver-notify-sent')

WXPAY_TRADE_TYPE_APP = 'APP'
WXPAY_TRADE_TYPE_JSAPI = 'JSAPI'
WXPAY_TRADE_TYPE_NATIVE = 'NATIVE'
NOTIFIED_FROM_ORDER_QUERY = 'order_query'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
SUCCESSFULLY_MARK = 'SUCCESS'  # wxpay require this 7 characters to be returned to them
FAILED_MARK = 'FAIL'
ORDER_PAID_MARK = 'ORDERPAID'
SYSTEMERROR_MARK = 'SYSTEMERROR'
QUERY_ORDER_STATUS_NOTPAY = 'NOTPAY'
QUERY_ORDER_STATUS_CLOSED = 'CLOSED'
QUERY_ORDER_STATUS_TO_IGNORE = {
    QUERY_ORDER_STATUS_NOTPAY,
    QUERY_ORDER_STATUS_CLOSED
}
WXPAY_BANK_TYPE = 'WX'
WXPAY_ORDER_QUERY_URL = 'https://api.mch.weixin.qq.com/pay/orderquery'
WXPAY_UNIFIEDORDER_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
WXPAY_CLOSE_TRADE_URL = 'https://api.mch.weixin.qq.com/pay/closeorder'
WXPAY_REFUND_QUERY_URL = 'https://api.mch.weixin.qq.com/pay/refundquery'
WXPAY_REFUND_URL = 'https://api.mch.weixin.qq.com/secapi/pay/refund'
WXPAY_REFUND_CHANNEL_ORIGINAL = 'ORIGINAL'
WXPAY_REFUND_CHANNEL_BALANCE = 'BALANCE'
WXPAY_REFUND_CHANNELS = {
    WXPAY_REFUND_CHANNEL_ORIGINAL: '原路退款',
    WXPAY_REFUND_CHANNEL_BALANCE: '退回到余额'
}

WXPAY_REFUND_TIMEOUT = 'WXPAY_REFUND_TIMEOUT'
WXPAY_REFUND_ERROR = 'WXPAY_REFUND_ERROR'

WXPAY_REFUND_STATUS_SUCCESS = 'SUCCESS'
WXPAY_REFUND_STATUS_CLOSED = 'REFUNDCLOSE'
WXPAY_REFUND_STATUS_PROCESSING = 'PROCESSING'
WXPAY_REFUND_STATUS_CHANGE = 'CHANGE'
WXPAY_REFUND_STATUS = {
    WXPAY_REFUND_STATUS_SUCCESS: '退款成功',
    WXPAY_REFUND_STATUS_PROCESSING: '退款处理中',
    WXPAY_REFUND_STATUS_CHANGE: '转入代发，需人工退款'
}


def make_wxpay_request_for_native(app_id, mch_id, api_key, out_trade_no, subject, body, total_fee, notify_url, time_start, time_expire, shopper_ip_address):
    wxpay_prepay_order = create_prepay_order(app_id, mch_id, api_key, WXPAY_TRADE_TYPE_NATIVE, out_trade_no, subject, body, total_fee, notify_url,
                                             shopper_ip_address, time_start, time_expire)
    return wxpay_prepay_order.code_url


def make_wxpay_request_for_app(app_id, mch_id, api_key, out_trade_no, subject, body, total_fee, notify_url, time_start, time_expire, shopper_ip_address):
    wxpay_prepay_order = create_prepay_order(app_id, mch_id, api_key, WXPAY_TRADE_TYPE_APP, out_trade_no, subject, body, total_fee, notify_url,
                                             shopper_ip_address, time_start, time_expire)
    wxpay_request = DictObject(appid=app_id, partnerid=mch_id, prepayid=wxpay_prepay_order.prepay_id, package='Sign=WXPay',
                               noncestr=wxpay_prepay_order.nonce_str, timestamp=str(get_current_timestamp()))
    wxpay_request.sign = sign_md5(wxpay_request, api_key)
    return wxpay_request


def make_wxpay_request_for_mp(app_id, mch_id, api_key, out_trade_no, subject, body, total_fee, notify_url, time_start, time_expire, shopper_ip_address, openid):
    wxpay_prepay_order = create_prepay_order(app_id, mch_id, api_key, WXPAY_TRADE_TYPE_JSAPI, out_trade_no, subject, body, total_fee, notify_url,
                                             shopper_ip_address, time_start, time_expire, openid=openid)
    wxpay_request = DictObject(appId=app_id, timeStamp=str(get_current_timestamp()), nonceStr=uuid4().get_hex(),
                               package='prepay_id={}'.format(wxpay_prepay_order.prepay_id), signType='MD5')
    wxpay_request.paySign = sign_md5(wxpay_request, api_key)
    return wxpay_request


def create_prepay_order(app_id, mch_id, api_key, trade_type, out_trade_no, subject, body, total_fee, notify_url, spbill_create_ip, time_start,
                        time_expire, openid=None):
    time_start_beijing_time_str = convert_datetime_to_client_timezone(time_start).strftime('%Y%m%d%H%M%S')
    time_expire_beijing_time_str = convert_datetime_to_client_timezone(time_expire).strftime('%Y%m%d%H%M%S')
    order = DictObject(appid=app_id, mch_id=mch_id, trade_type=trade_type, out_trade_no=out_trade_no, body=subject, detail=body,
                       total_fee=unicode(int(total_fee * 100)), spbill_create_ip=spbill_create_ip, time_start=time_start_beijing_time_str,
                       time_expire=time_expire_beijing_time_str, notify_url=notify_url, nonce_str=uuid4().get_hex(), goods_tag=None, product_id=None,
                       fee_type=None, limit_pay=None, device_info=None, openid=openid)
    order.sign = sign_md5(order, api_key)
    with require_current_template_directory_relative_to():
        data = to_str(get_template('unified-order.xml').render(order=order))
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(WXPAY_UNIFIEDORDER_URL, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('wxpay unified order exception-thrown: %(out_trade_no)s, %(data)s', {'out_trade_no': out_trade_no, 'data': data})
        raise
    else:
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay unified order got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise Exception('wxpay unified order got failed response: {}'.format(parsed_response.return_msg))
        try:
            verify_wxpay_response(parsed_response, api_key)
        except Exception:
            LOGGER.info('wxpay unified order got fake response: %(data)s', {'data': data})
            raise
        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay unified order got failed result: %(err_code)s, %(err_code_des)s, %(data)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data
            })
            if parsed_response.result_code == ORDER_PAID_MARK:
                raise WXPayException('订单已支付完成')
            if parsed_response.result_code == SYSTEMERROR_MARK:
                raise WXPayException(parsed_response.err_code_des)
            if parsed_response.err_code_des:
                raise WXPayException(parsed_response.err_code_des)
            raise WXPayException('支付遇到错误，请稍后重试')
        LOGGER.info('wxpay unified order success: %(response)s', {'response': response.content})
        return DictObject(nonce_str=parsed_response.nonce_str, trade_type=parsed_response.trade_type, prepay_id=parsed_response.prepay_id,
                          code_url=parsed_response.get('code_url'))


def close_order(app_id, mch_id, api_key, out_trade_no):
    kwargs = DictObject(appid=app_id, mch_id=mch_id, nonce_str=uuid4().get_hex(), out_trade_no=out_trade_no)
    kwargs.sign = sign_md5(kwargs, api_key)
    with require_current_template_directory_relative_to():
        data = to_str(get_template('close-trade.xml').render(**kwargs))
    headers = {'Content-Type': 'application/xml'}
    response = None
    try:
        response = requests.post(WXPAY_CLOSE_TRADE_URL, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('wxpay close trade exception-thrown: %(out_trade_no)s, %(data)s', {
            'out_trade_no': out_trade_no,
            'data': data,
            'response': response.content if response else ''
        })
        raise
    else:
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay close trade got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise Exception('wxpay close trade got failed response: {}'.format(parsed_response.return_msg))
        try:
            verify_wxpay_response(parsed_response, api_key)
        except Exception:
            LOGGER.info('wxpay close trade got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise
        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay close trade got failed result: %(err_code)s, %(err_code_des)s, %(data)s, %(response)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data,
                'response': response.content
            })
        LOGGER.info('wxpay close trade success: %(out_trade_no)s, %(response)s', {'out_trade_no': out_trade_no, 'response': response.content})


def verify_wxpay_response(parsed_response, api_key):
    sign = parsed_response.pop('sign', None)
    if sign != sign_md5(parsed_response, api_key):
        raise Exception('invalid sign')


def process_wxpay_payment_notification(app_id, mch_id, api_key, arguments, notified_from):
    out_trade_no, trade_no, buyer_id, paid_total, paid_at, bank_code, bank_billno, show_url, discarded_reasons = validate_payment_notification(app_id, mch_id, api_key, arguments)
    if discarded_reasons:
        LOGGER.warn('wxpay payment notification discarded: %(discarded_reasons)s, %(arguments)s', {
            'discarded_reasons': discarded_reasons,
            'arguments': arguments
        })
        set_http_status_code(httplib.BAD_REQUEST)
        return_code = FAILED_MARK
        return_msg = ', '.join(discarded_reasons)
    else:
        return_code = SUCCESSFULLY_MARK
        return_msg = 'OK'
        publish_event(EVENT_WXPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
                      paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=bank_code, bank_billno=bank_billno, show_url=show_url,
                      notified_from=notified_from)
    with require_current_template_directory_relative_to():
        return get_template('notification-return.xml').render(return_code=return_code, return_msg=return_msg)


def query_order_status(app_id, mch_id, api_key, out_trade_no):
    paid = False
    args = DictObject(appid=app_id, mch_id=mch_id, out_trade_no=out_trade_no, nonce_str=uuid4().get_hex())
    args.sign = sign_md5(args, api_key)
    with require_current_template_directory_relative_to():
        data = to_str(get_template('query-order.xml').render(**args))
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(WXPAY_ORDER_QUERY_URL, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('wxpay order query exception-thrown: %(out_trade_no)s, %(data)s', {'out_trade_no': out_trade_no, 'data': data})
        raise
    else:
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay query order status got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise Exception('wxpay query order status got failed response: {}'.format(parsed_response.return_msg))
        try:
            verify_wxpay_response(parsed_response, api_key)
        except Exception:
            LOGGER.info('wxpay query order status got fake response: %(data)s', {'data': data})
            raise
        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.info('wxpay query order status got failed result: %(err_code)s, %(err_code_des)s, %(data)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data
            })
            raise Exception('wxpay query order status got failed result: {}, {}'.format(parsed_response.err_code, parsed_response.err_code_des))

        trade_no, paid_total, paid_at, bank_billno, errors = validate_order_info(parsed_response)
        if errors:
            if parsed_response.trade_state not in QUERY_ORDER_STATUS_TO_IGNORE:
                LOGGER.error('wxpay query order status invalid info found: %(errors)s, %(response)s', {
                    'errors': errors,
                    'response': response.content
                })
        else:
            LOGGER.debug(parsed_response)
            publish_event(EVENT_WXPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=None,
                          paid_total=paid_total, paid_at=paid_at, payment_channel_bank_code=None, bank_billno=bank_billno, show_url=None,
                          notified_from=NOTIFIED_FROM_ORDER_QUERY)
            paid = True
    return paid


def validate_order_info(arguments):
    errors = []
    trade_no = arguments.get('transaction_id')
    if not trade_no:
        errors.append('no transaction_id')
    paid_total = arguments.get('total_fee')
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            errors.append('invalid total_fee: {}'.format(paid_total))
    else:
        errors.append('no total_fee')
    paid_at = arguments.get('time_end')
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except Exception:
            errors.append('invalid time_end: {}'.format(paid_at))
    else:
        errors.append('no time_end')
    bank_billno = None
    return trade_no, paid_total, paid_at, bank_billno, errors


def validate_payment_notification(app_id, mch_id, api_key, arguments):
    discarded_reasons = []
    if not (VEIL_ENV.is_dev or VEIL_ENV.is_test):
        if not is_sign_correct(arguments, api_key):
            discarded_reasons.append('sign is incorrect')
    if mch_id != arguments.get('mch_id'):
        discarded_reasons.append('mch_id mismatched')
    if app_id != arguments.get('appid'):
        discarded_reasons.append('app_id mismatched')
    if arguments.get('result_code') != SUCCESSFULLY_MARK:
        LOGGER.info('wxpay got failed notification: %(err_code)s, %(err_code_des)s', {'err_code': arguments.err_code, 'err_code_des': arguments.err_code_des})
        discarded_reasons.append('trade not succeeded')
    out_trade_no = arguments.get('out_trade_no')
    if not out_trade_no:
        discarded_reasons.append('no out_trade_no')
    trade_no = arguments.get('transaction_id')
    if not trade_no:
        discarded_reasons.append('no transaction_id')
    paid_total = arguments.get('total_fee')
    if paid_total:
        try:
            paid_total = Decimal(paid_total) / 100
        except DecimalException:
            discarded_reasons.append('invalid total_fee: {}'.format(paid_total))
    else:
        discarded_reasons.append('no total_fee')
    paid_at = arguments.get('time_end')  # 支付完成时间，时区为GMT+8 beijing，格式为yyyymmddhhmmss
    if paid_at:
        try:
            paid_at = to_datetime(format='%Y%m%d%H%M%S')(paid_at)
        except Exception:
            discarded_reasons.append('invalid time_end: {}'.format(paid_at))
    else:
        discarded_reasons.append('no time_end')
    buyer_alias = arguments.get('openid')
    bank_code = arguments.get('bank_type')
    bank_billno = None
    return out_trade_no, trade_no, buyer_alias, paid_total, paid_at, bank_code, bank_billno, None, discarded_reasons


def is_sign_correct(arguments, key):
    sign = arguments.pop('sign', None)
    if not sign or sign.upper() != sign_md5(arguments, key):
        return False
    return True


def sign_md5(params, key):
    param_str = '{}&key={}'.format('&'.join('{}={}'.format(key, params[key]) for key in sorted(params) if params[key]), key)
    return hashlib.md5(param_str.encode('UTF-8')).hexdigest().upper()


def parse_xml_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments


def refund(out_trade_no, out_refund_no, total_fee, refund_fee):
    """
    request wxpay refund

    :param out_trade_no: 原交易外部订单号
    :param out_refund_no: 外部退款单号
    :param total_fee: 原交易金额, Decimal
    :param refund_fee: 退款金额, Decimal
    :return:
        DictObject(out_trade_no: 商户订单号, out_refund_no: 商户退款单号, refund_id: 退款id, refund_channel_text: 退款去向（原支付卡/余额）,
            refund_fee: 申请退款金额, settlement_refund_fee: 扣除非充值的代金券后实际退款金额（APP微信退款接口无该字段，这里保留该字段，值与refund_fee一致）)
    """
    if refund_fee > total_fee:
        raise WXRefundException(WXPAY_REFUND_ERROR, 'refund_fee can not be greater than total_fee')

    config = wxpay_client_config()
    refund_request = DictObject(appid=config.app_id, mch_id=config.mch_id, nonce_str=uuid4().get_hex(), out_trade_no=out_trade_no, out_refund_no=out_refund_no,
                                total_fee=unicode(int(total_fee * 100)), refund_fee=unicode(int(refund_fee * 100)), op_user_id=config.mch_id)
    refund_request.sign = sign_md5(refund_request, config.api_key)
    with require_current_template_directory_relative_to():
        data = to_str(get_template('refund.xml').render(refund_request=refund_request))
    headers = {'Content-Type': 'application/xml'}
    response = None
    try:
        response = requests.post(WXPAY_REFUND_URL, data=data, headers=headers, cert=(config.api_client_cert, config.api_client_key), timeout=(3.05, 9),
                                 max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('request wxpay refund got read timeout: %(data)s', {'data': data})
        raise WXRefundException(WXPAY_REFUND_TIMEOUT, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('request wxpay refund got exception: %(out_trade_no)s, %(out_refund_no)s, %(data)s, %(response)s', {
            'out_trade_no': out_trade_no,
            'out_refund_no': out_refund_no,
            'data': data,
            'response': response.content if response else e.message
        })
        raise WXRefundException(WXPAY_REFUND_ERROR, response.content if response else e.message)
    else:
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.error('request wxpay refund got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise WXRefundException(WXPAY_REFUND_ERROR, parsed_response.return_msg)
        try:
            verify_wxpay_response(parsed_response, config.api_key)
        except Exception:
            LOGGER.error('request wxpay refund got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise WXRefundException(WXPAY_REFUND_ERROR, 'sign is incorrect')
        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.error('request wxpay refund got failed result: %(err_code)s, %(err_code_des)s, %(data)s, %(response)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data,
                'response': response.content
            })
            raise WXRefundException(parsed_response.result_code, parsed_response.err_code_des)
        if parsed_response.out_trade_no != out_trade_no:
            raise WXRefundException(WXPAY_REFUND_ERROR, 'out trade no mismatch')
        if parsed_response.out_refund_no != out_refund_no:
            raise WXRefundException(WXPAY_REFUND_ERROR, 'out refund no mismatch')
        if refund_fee != Decimal(parsed_response.refund_fee) / 100:
            raise WXRefundException(WXPAY_REFUND_ERROR, 'refund fee mismatch')

        _refund_fee = Decimal(parsed_response.refund_fee) / 100
        settlement_refund_fee = parsed_response.get('settlement_refund_fee')
        if settlement_refund_fee:
            settlement_refund_fee = Decimal(settlement_refund_fee) / 100
        else:
            settlement_refund_fee = _refund_fee
        refund_channel_text = None
        refund_channel = parsed_response.get('refund_channel')
        if refund_channel:
            refund_channel_text = WXPAY_REFUND_CHANNELS[refund_channel]
        LOGGER.info('request wxpay refund success: %(response)s', {'response': response.content})
        return DictObject(out_trade_no=parsed_response.out_trade_no, out_refund_no=parsed_response.out_refund_no,
                          refund_id=parsed_response.refund_id, refund_channel_text=refund_channel_text, refund_fee=_refund_fee,
                          settlement_refund_fee=settlement_refund_fee)


def query_refund_status(out_refund_no):
    """
    query wxpay refund status

    :param out_refund_no: 退款单号
    :return:
        [DictObject(out_refund_no: 外部退款单号, refund_id: 退款id,
            refund_channel_text: 退款去向（原支付卡/余额）, refund_fee: 申请退款金额, settlement_refund_fee: 扣除非充值的代金券后实际退款金额, refund_status: 退款状态,
            refund_status_text: 退款状态文字（成功/失败/处理中/转代发）, refund_recv_accout: 退款入账账户(某张卡/用户零钱)), ...]
    """
    config = wxpay_client_config()
    query_request = DictObject(appid=config.app_id, mch_id=config.mch_id, nonce_str=uuid4().get_hex(), out_refund_no=out_refund_no)
    query_request.sign = sign_md5(query_request, config.api_key)
    with require_current_template_directory_relative_to():
        data = to_str(get_template('query-refund.xml').render(query_request=query_request))
    headers = {'Content-Type': 'application/xml'}
    response = None
    try:
        response = requests.post(WXPAY_REFUND_QUERY_URL, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('query wxpay refund status got read timeout: %(data)s', {'data': data})
        raise WXRefundException(WXPAY_REFUND_TIMEOUT, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('query wxpay refund status got exception: %(out_refund_no)s, %(data)s, %(response)s', {
            'out_refund_no': out_refund_no,
            'data': data,
            'response': response.content if response else ''
        })
        raise WXRefundException(WXPAY_REFUND_ERROR, 'read response but timeout')
    else:
        LOGGER.debug(response.content)
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.error('query wxpay refund status got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise WXRefundException(WXPAY_REFUND_ERROR, parsed_response.return_msg)
        try:
            verify_wxpay_response(parsed_response, config.api_key)
        except Exception:
            LOGGER.error('query wxpay refund status got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise WXRefundException(WXPAY_REFUND_ERROR, 'sign is incorrect')
        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.error('query wxpay refund status got failed result: %(err_code)s, %(err_code_des)s, %(data)s, %(response)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data,
                'response': response.content
            })
            raise WXRefundException(WXPAY_REFUND_ERROR, parsed_response.err_code_des)
        LOGGER.info('query wxpay refund status success: %(response)s', {'response': response.content})
        _refund_status = parsed_response.get('refund_status_0')
        refund_status_text = WXPAY_REFUND_STATUS[_refund_status]
        success = _refund_status == WXPAY_REFUND_STATUS_SUCCESS
        closed = _refund_status == WXPAY_REFUND_STATUS_CLOSED
        processing = _refund_status == WXPAY_REFUND_STATUS_PROCESSING
        failed = _refund_status == WXPAY_REFUND_STATUS_CHANGE

        refund_channel_text = None
        refund_channel = parsed_response.get('refund_channel_0')
        if refund_channel:
            refund_channel_text = WXPAY_REFUND_CHANNELS[refund_channel]

        refund_fee = Decimal(parsed_response.get('refund_fee_0')) / 100
        settlement_refund_fee = parsed_response.get('settlement_refund_fee_0')
        if settlement_refund_fee:
            settlement_refund_fee = Decimal(settlement_refund_fee) / 100
        else:
            settlement_refund_fee = refund_fee

        refund_time_text = parsed_response.get('refund_success_time_0')
        return DictObject(
            success=success,
            closed=closed,
            processing=processing,
            failed=failed,
            refund_status_text=refund_status_text,
            out_trade_no=parsed_response.out_trade_no,
            out_refund_no=parsed_response.get('out_refund_no_0'),
            refund_id=parsed_response.get('refund_id_0'),
            refund_channel_text=refund_channel_text,
            refund_fee=refund_fee,
            refund_time=to_datetime_via_parse(refund_time_text) if refund_time_text else None,
            settlement_refund_fee=settlement_refund_fee,
            refund_recv_accout=parsed_response.get('refund_recv_accout_0'))


class InvalidWXAccessToken(Exception):
    pass


class WXPayException(Exception):
    pass


class WXRefundException(Exception):
    def __init__(self, code, reason):
        super(WXRefundException, self).__init__()
        self.code = code
        self.reason = reason

    @property
    def is_timeout(self):
        return self.code in {WXPAY_REFUND_TIMEOUT, SYSTEMERROR_MARK}  # 处理超时

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, reason: {}'.format(self.code, self.reason)

    def __str__(self):
        return self.__unicode__().encode('utf-8')
