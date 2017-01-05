# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import hashlib
import logging
from decimal import Decimal, DecimalException

import lxml.objectify

from veil.frontend.cli import *
from veil.profile.model import *
from veil.profile.web import *
from .tenpay_client_installer import tenpay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_TENPAY_TRADE_PAID = define_event('tenpay-trade-paid')  # valid notification
EVENT_TENPAY_REFUND_NOTIFIED = define_event('tenpay-refund-notified')

PAYMENT_URL = 'https://gw.tenpay.com/gateway/pay.htm'
VERIFY_URL = 'https://gw.tenpay.com/gateway/simpleverifynotifyid.xml'
PAYMENT_QUERY_URL = 'https://gw.tenpay.com/gateway/normalorderquery.xml'
REFUND_URL = 'https://api.mch.tenpay.com/refundapi/gateway/refund.xml'
REFUND_QUERY_URL = 'https://gw.tenpay.com/gateway/normalrefundquery.xml'

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFIED_FROM_PAYMENT_QUERY = 'payment_query'
NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success'  # tenpay require this 7 characters to be returned to them
TENPAY_REFUND_STATUS_SUCCESS_MARKS = {'4', '10'}
TENPAY_REFUND_STATUS_FAIL_MARKS = {'3', '5', '6'}
TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK = '9'
TENPAY_REFUND_STATUS_PROCESSING_MARKS = {'8', TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK, '11'}
TENPAY_REFUND_STATUS_NEED_RETRY_MARKS = {'1', '2'}
TENPAY_REFUND_STATUS_MANUAL = '7'
TENPAY_REFUND_CHANNEL_TENPAY = '0'
TENPAY_REFUND_CHANNEL_BANK = '1'
TENPAY_REFUND_CHANNELS = {
    TENPAY_REFUND_CHANNEL_TENPAY: '退到财付通',
    TENPAY_REFUND_CHANNEL_BANK: '退到银行'
}


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
    if not (VEIL_ENV.is_dev or VEIL_ENV.is_test):
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
            LOGGER.debug('tenpay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.content, 'verify_url': response.url})
        else:
            LOGGER.warn('tenpay notify verify failed: %(response)s, %(verify_url)s', {'response': response.content, 'verify_url': response.url})
            error = 'notification not from tenpay'
    return error


def parse_xml_response(response):
    arguments = DictObject()
    root = lxml.objectify.fromstring(response)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments


def refund(out_trade_no, out_refund_no, total_fee, refund_fee, notify_url=None):
    """
    tenpay refund

    :param out_trade_no: 原交易外部订单号
    :param out_refund_no: 外部退款单号
    :param total_fee: 原交易金额, Decimal
    :param refund_fee: 退款金额, Decimal
    :param notify_url: 异步通知URL
    :return:
        DictObject(request_success=False, reason=...)
        DictObject(request_success=True, success=True/False, failed=True/False, processing=True/False, out_trade_no: 原交易外部订单号, out_refund_no: 外部退款单号,
            refund_id: 退款id, refund_status_text:退款状态（成功/失败/处理中/需人工处理）, refund_fee: 退款金额, refund_channel_text: 退款去向（财付通/银行卡）,
            recv_user_id: 接收退款的财付通账号, reccv_user_name: 接收退款的姓名)
    """
    config = tenpay_client_config()
    partner_id = config.partner_id
    op_user_id = config.refund_op_user_id
    op_user_passwd = hashlib.md5(config.refund_op_user_password).hexdigest()
    data = DictObject(input_charset='UTF-8',
                      service_version='1.1',
                      partner=partner_id,
                      out_trade_no=out_trade_no,
                      out_refund_no=out_refund_no,
                      total_fee=unicode(int(total_fee * 100)),
                      refund_fee=unicode(int(refund_fee * 100)),
                      op_user_id=op_user_id,
                      op_user_passwd=op_user_passwd)
    if notify_url:
        data.notify_url = notify_url
    data.sign = sign_md5(data)
    response = None
    try:
        response = requests.get(REFUND_URL, data=data, verify=config.api_ca_cert, cert=(config.api_client_cert, config.api_client_key),
                                timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('request tenpay refund got read timeout: %(data)s', {'data': data})
        return DictObject(request_success=False, reason='read response but timeout')
    except Exception as e:
        LOGGER.exception('request tenpay refund got exception: %(data)s, %(response)s', {'data': data, 'response': response.content if response else ''})
        return DictObject(request_success=False, reason=response.content if response else e.message)
    else:
        result = parse_xml_response(response.content)
        assert result.input_charset == 'UTF-8', 'assume tenpay use same input charset as request'
        assert result.sign_type == 'MD5', 'assume tenpay use same sign type as request'
        if not is_sign_correct(result):
            LOGGER.error('request tenpay refund got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            return DictObject(request_success=False, reason='sign is incorrect')
        if result.retcode != '0':
            LOGGER.error('request tenpay refund got failed response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            return DictObject(request_success=False, reason=result.retmsg)

        reason = None
        if result.partner != partner_id:
            reason = 'partner mismatch'
        elif result.out_trade_no != out_trade_no:
            reason = 'out trade no mismatch'
        elif result.out_refund_no != out_refund_no:
            reason = 'out refund no mismatch'
        elif result.refund_fee != str(int(refund_fee * 100)):
            reason = 'refund fee mismatch'
        if reason:
            LOGGER.error('request tenpay refund got invalid response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            return DictObject(request_success=False, reason=reason)

        if result.refund_status in TENPAY_REFUND_STATUS_NEED_RETRY_MARKS:
            LOGGER.error('request tenpay refund got need retry response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            return DictObject(request_success=False, reason='请重试')

        ret_data = DictObject(request_success=True,
                              success=result.refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS,
                              failed=result.refund_status in TENPAY_REFUND_STATUS_FAIL_MARKS or result.refund_status == TENPAY_REFUND_STATUS_MANUAL,
                              processing=result.refund_status in TENPAY_REFUND_STATUS_PROCESSING_MARKS | TENPAY_REFUND_STATUS_NEED_RETRY_MARKS,
                              out_trade_no=out_trade_no,
                              out_refund_no=out_refund_no,
                              refund_id=result.refund_id,
                              refund_fee=refund_fee,
                              refund_channel_text=TENPAY_REFUND_CHANNELS[result.refund_channel],
                              recv_user_id=result.get('recv_user_id'),
                              reccv_user_name=result.get('reccv_user_name'))
        if ret_data.success:
            ret_data.refund_status_text = '退款成功'
        elif ret_data.failed:
            ret_data.refund_status_text = '退款失败'
            if result.refund_status == TENPAY_REFUND_STATUS_MANUAL:
                ret_data.refund_status_text = '退款失败：转入代发，需人工退款'
        elif ret_data.processing:
            ret_data.refund_status_text = '退款处理中'
            if result.refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
                ret_data.refund_status_text = '退款处理中：已提交退款请求给银行'
        else:
            raise Exception('unknown refund status:{}'.format(result.refund_status))
        return ret_data


def process_refund_notification(arguments):
    """
    tenpay refund asynchronous notification handler

    只有退款成功/需人工处理/已提交请求给银行才可以收到通知

    :param arguments: all arguments submitted to notify_url
    :return:
        success / fail
        publish event if success, arguments are same as refund
    """
    if not is_sign_correct(arguments):
        return 'sign is incorrect'
    if arguments.partner != tenpay_client_config().partner_id:
        return 'partner id mismatch'
    ret_data = DictObject(
        request_success=True,
        sucesss=arguments.refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS,
        failed=arguments.refund_status in TENPAY_REFUND_STATUS_FAIL_MARKS or arguments.refund_status == TENPAY_REFUND_STATUS_MANUAL,
        processing=arguments.refund_status in TENPAY_REFUND_STATUS_PROCESSING_MARKS | TENPAY_REFUND_STATUS_NEED_RETRY_MARKS,
        out_trade_no=arguments.out_trade_no,
        out_refund_no=arguments.out_refund_no,
        refund_id=arguments.refund_id,
        refund_fee=Decimal(arguments.refund_fee) / 100,
        refund_channel_text=TENPAY_REFUND_CHANNELS[arguments.refund_channel],
        recv_user_id=arguments.get('recv_user_id'),
        reccv_user_name=arguments.get('reccv_user_name'))
    if ret_data.success:
        ret_data.refund_status_text = '退款成功'
    elif ret_data.failed:
        ret_data.refund_status_text = '退款失败'
        if arguments.refund_status == TENPAY_REFUND_STATUS_MANUAL:
            ret_data.refund_status_text = '退款失败：转入代发，需人工退款'
    elif ret_data.processing:
        ret_data.refund_status_text = '退款处理中'
        if arguments.refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
            ret_data.refund_status_text = '退款处理中：已提交退款请求给银行'
    else:
        raise Exception('unknown refund status:{}'.format(arguments.refund_status))
    publish_event(EVENT_TENPAY_REFUND_NOTIFIED, refund_result=ret_data)
    return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


def query_refund_status(out_refund_no):
    """
    query refund status

    :param out_refund_no: 退款单号
    :return:
        DictObject(request_success=False, reason=...)
        DictObject(request_success=True, refund_status=[DictObject(success:, processing:, out_trade_no: 原交易外部订单号, out_refund_no: 外部退款单号,
            refund_id: 退款id, refund_status_text:退款状态（成功/失败/处理中/需人工处理）, refund_fee: 退款金额, refund_channel_text: 退款去向（财付通/银行卡）,
            recv_user_id: 接收退款的财付通账号, reccv_user_name: 接收退款的姓名, refund_time_begin: 申请退款时间(UTC), refund_time_last_modify: 退款最后修改时间(UTC)),
            ...])
    """
    params = DictObject(input_charset='UTF-8', service_version='1.1', partner=tenpay_client_config().partner_id, out_refund_no=out_refund_no)
    params.sign = sign_md5(params)
    response = None
    try:
        response = requests.get(REFUND_QUERY_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('query tenpay refund status got read timeout: %(params)s', {'params': params})
        return DictObject(request_success=False, reason='read response but timeout')
    except Exception as e:
        LOGGER.exception('query tenpay refund status got exception: %(params)s, %(response)s', {
            'params': params,
            'response': response.content if response else ''
        })
        return DictObject(request_success=False, reason=response.content if response else e.message)
    else:
        result = parse_xml_response(response.content)
        assert result.input_charset == 'UTF-8', 'assume tenpay use same input charset as request'
        assert result.sign_type == 'MD5', 'assume tenpay use same sign type as request'
        if not is_sign_correct(result):
            LOGGER.error('query tenpay refund status got fake response: %(params)s, %(response)s', {'params': params, 'response': response.content})
            return DictObject(request_success=False, reason='sign is incorrect')
        if result.retcode != '0':
            if result.retcode == '88222014':
                return DictObject(request_success=False, reason='退款失败：订单未退款')
            if result.retcode == '88221009':
                return DictObject(request_success=False, reason='退款失败：订单不存在')
            LOGGER.error('query tenpay refund status got failed response: %(params)s, %(response)s', {'params': params, 'response': response.content})
            return DictObject(request_success=False, reason=result.retmsg)
        refund_status = []
        for i in range(int(result.refund_count)):
            _refund_status = result.get('refund_state_{}'.format(i))
            if _refund_status in TENPAY_REFUND_STATUS_NEED_RETRY_MARKS:
                continue
            success = _refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS
            failed = _refund_status in TENPAY_REFUND_STATUS_FAIL_MARKS or _refund_status == TENPAY_REFUND_STATUS_MANUAL
            processing = _refund_status in TENPAY_REFUND_STATUS_PROCESSING_MARKS | TENPAY_REFUND_STATUS_NEED_RETRY_MARKS
            if success:
                refund_status_text = '退款成功'
            elif failed:
                refund_status_text = '退款失败'
                if _refund_status == TENPAY_REFUND_STATUS_MANUAL:
                    refund_status_text = '退款失败：转入代发，需人工退款'
            elif processing:
                refund_status_text = '退款处理中'
                if _refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
                    refund_status_text = '退款处理中：已提交退款请求给银行'
            else:
                LOGGER.error('query tenpay refund status got unknown status: %(params)s, %(response)s', {'params': params, 'response': response.content})
                raise Exception('unknown refund status: {}'.format(_refund_status))
            refund_time_begin = result.get('refund_time_begin_{}'.format(i))
            if refund_time_begin:
                refund_time_begin = to_datetime(format='%Y%m%d%H%M%S')(refund_time_begin)
            refund_time_last_modify = result.get('refund_time_{}'.format(i))
            if refund_time_last_modify:
                refund_time_last_modify = to_datetime(format='%Y%m%d%H%M%S')(refund_time_last_modify)
            refund_status.append(DictObject(
                success=success,
                failed=failed,
                processing=processing,
                refund_status_text=refund_status_text,
                out_trade_no=result.out_trade_no,
                out_refund_no=result.get('out_refund_no_{}'.format(i)),
                refund_id=result.get('refund_id_{}'.format(i)),
                refund_fee=Decimal(result.get('refund_fee_{}'.format(i))) / 100,
                refund_channel_text=TENPAY_REFUND_CHANNELS[result.get('refund_channel_{}'.format(i))],
                recv_user_id=result.get('recv_user_id_{}'.format(i)),
                reccv_user_name=result.get('reccv_user_name_{}'.format(i)),
                refund_time_begin=refund_time_begin,
                refund_time_last_modify=refund_time_last_modify
            ))
        return DictObject(request_success=True, refund_status=refund_status)
