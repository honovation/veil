# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import base64
import hashlib
import logging
import urllib
from decimal import Decimal, DecimalException

import lxml.objectify
import rsa

from veil.frontend.cli import *
from veil.profile.model import *
from veil.profile.web import *
from veil.utility.xml import *
from .alipay_client_installer import alipay_client_config

LOGGER = logging.getLogger(__name__)

EVENT_ALIPAY_TRADE_PAID = define_event('alipay-trade-paid')  # valid notification
EVENT_ALIPAY_REFUND_NOTIFIED = define_event('alipay-refund-notified')
EVENT_ALIPAY_DBACK_NOTIFIED = define_event('alipay-dback-notified')

PAYMENT_URL = 'https://mapi.alipay.com/gateway.do'
VERIFY_URL = PAYMENT_URL
REFUND_URL = PAYMENT_URL

NOTIFIED_FROM_RETURN_URL = 'return_url'
NOTIFIED_FROM_NOTIFY_URL = 'notify_url'
NOTIFIED_FROM_PAYMENT_QUERY = 'payment_query'

NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK = 'success'  # alipay require this 7 characters to be returned to them

ALIPAY_REFUND_SEQ_NO_LENGTH_MIN = 3
ALIPAY_REFUND_SEQ_NO_LENGTH_MAX = 24
ALIPAY_REFUND_DATA_LIST_LENGTH_MAX = 1000

ALIPAY_REFUND_RESPONSE_SUCCESS_MARK = 'T'
ALIPAY_REFUND_RESPONSE_FAIL_MARK = 'F'
ALIPAY_REFUND_RESPONSE_PROCESSING_MARK = 'P'

ALIPAY_REFUND_TIMEOUT = 'ALIPAY_REFUND_TIMEOUT'
ALIPAY_REFUND_ERROR = 'ALIPAY_REFUND_ERROR'
ALIPAY_REFUND_DUPLICATE_BATCH_NO = 'DUPLICATE_BATCH_NO'

ALIPAY_REFUND_RESULT_SUCCESS_MARK = 'SUCCESS'

ALIPAY_DBACK_RESULT_SUCCESS_MARK = 'S'
ALIPAY_DBACK_RESULT_FAIL_MARK = 'F'
ALIPAY_DBACK_RESULT_WAITING_MARK = 'I'


ALIPAY_REQUEST_REFUND_PROCESSING = 'ALIPAY_REQUEST_REFUND_PROCESSING'

ALIPAY_REFUND_INIT = 'INIT'  # 退款申请成功,等待处理
ALIPAY_REFUND_PROCESSING = 'PROCESSING'  # 退款正在处理中


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


def create_alipay_wap_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, minutes_to_expire):
    params = dict(service='alipay.wap.create.direct.pay.by.user',
                  partner=alipay_client_config().partner_id,
                  _input_charset='UTF-8',
                  notify_url=notify_url,
                  return_url=return_url,
                  out_trade_no=out_trade_no,
                  subject=subject,
                  total_fee='{:.2f}'.format(total_fee),
                  seller_id=alipay_client_config().partner_id,
                  payment_type='1',
                  show_url=show_url,
                  body=body,
                  it_b_pay='{}m'.format(minutes_to_expire),
                  app_pay='Y')
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    return '{}?{}'.format(PAYMENT_URL, urlencode(params))


def create_alipay_payment_url(out_trade_no, subject, body, total_fee, show_url, return_url, notify_url, minutes_to_expire, shopper_ip_address):
    params = dict(service='create_direct_pay_by_user', partner=alipay_client_config().partner_id, _input_charset='UTF-8', out_trade_no=out_trade_no,
                  subject=subject, payment_type='1', seller_email=alipay_client_config().seller_email, total_fee='{:.2f}'.format(total_fee), body=body,
                  show_url=show_url, return_url=return_url, notify_url=notify_url, paymethod='directPay', exter_invoke_ip=shopper_ip_address,
                  extra_common_param=show_url, it_b_pay='{}m'.format(minutes_to_expire))
    params['sign'] = sign_md5(params)
    params['sign_type'] = 'MD5'
    return '{}?{}'.format(PAYMENT_URL, urlencode(params))


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
        LOGGER.debug(response.content)
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
    with_notify_id = NOTIFIED_FROM_PAYMENT_QUERY != notified_from
    trade_no, buyer_id, paid_total, paid_at, show_url, discarded_reasons = validate_payment_notification(out_trade_no, arguments, with_notify_id)
    if discarded_reasons:
        LOGGER.warn('alipay trade notification discarded: %(discarded_reasons)s, %(arguments)s', {
            'discarded_reasons': discarded_reasons,
            'arguments': arguments
        })
    else:
        publish_event(EVENT_ALIPAY_TRADE_PAID, out_trade_no=out_trade_no, payment_channel_trade_no=trade_no, payment_channel_buyer_id=buyer_id,
                      paid_total=paid_total, paid_at=paid_at, show_url=show_url, notified_from=notified_from)
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
        if not arguments.get('sign_type'):
            discarded_reasons.append('no sign_type')
        else:
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
    if alipay_client_config().partner_id != arguments.get('seller_id'):
        discarded_reasons.append('seller id mismatched')
    if arguments.get('seller_email') and alipay_client_config().seller_email != arguments.seller_email:
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
        if str('true') == response.content:
            LOGGER.debug('alipay notify verify succeeded: %(response)s, %(verify_url)s', {'response': response.content, 'verify_url': response.url})
        else:
            LOGGER.warn('alipay notify verify failed: %(response)s, %(verify_url)s', {'response': response.content, 'verify_url': response.url})
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
            'response': response.content if response else ''
        })
        raise
    else:
        arguments = lxml.objectify.fromstring(response.content)
        if arguments.is_success == 'T':
            LOGGER.info('alipay trade closed: %(out_trade_no)s, %(response)s', {
                'out_trade_no': out_trade_no,
                'response': response.content
            })
        else:
            LOGGER.warn('alipay trade close failed: %(out_trade_no)s, %(params)s, %(error)s', {
                'out_trade_no': out_trade_no,
                'params': params,
                'error': arguments.error
            })


def refund(out_refund_no, trade_no, amount, reason, notify_url=None, dback_notify_url=None):
    """
    alipay refund interface without password

    :param out_refund_no: 批量退款流水号（最大24位），用来生成batch_no
    :param trade_no: 原支付宝交易号
    :param amount: 退款金额，Decimal
    :param reason: 退款原因，不能包含: ^, |, $, #
    :param notify_url: 退款结果异步通知URL
    :param dback_notify_url: 充退结果异步通知URL
    :return batch_no: 退款批次号
    """
    if len(str(out_refund_no)) > ALIPAY_REFUND_SEQ_NO_LENGTH_MAX:
        raise ALIPayRefundException(ALIPAY_REFUND_ERROR, '流水号超过上限')
    if any(e in reason for e in {'^', '|', '$', '#'}):
        raise ALIPayRefundException(ALIPAY_REFUND_ERROR, '退款原因不能包含：^, |, $, #')
    refund_time = get_current_time_in_client_timezone()
    batch_no = '{}{}'.format(refund_time.strftime('%Y%m%d'), str(out_refund_no).zfill(ALIPAY_REFUND_SEQ_NO_LENGTH_MIN))
    detail_data = '{}^{:f}^{}'.format(trade_no, amount, reason)
    params = DictObject(
        service='refund_fastpay_by_platform_nopwd',
        partner=alipay_client_config().partner_id,
        _input_charset='UTF-8',
        batch_no=batch_no,
        refund_date=refund_time.strftime('%Y-%m-%d %H:%M:%S'),
        batch_num=1,
        detail_data=detail_data)
    if notify_url:
        params.notify_url = notify_url
    if dback_notify_url:
        params.dback_notify_url = dback_notify_url
    params.sign = sign_md5(params)
    params.sign_type = 'MD5'

    response = None
    try:
        response = requests.get(REFUND_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('request alipay refund got read timeout: %(params)s', {'params': params})
        raise ALIPayRefundException(ALIPAY_REFUND_TIMEOUT, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('request alipay refund got exception: %(response)s, %(params)s, %(message)s', {
            'response': response.content if response else '',
            'params': params,
            'message': e.message
        })
        raise ALIPayRefundException(ALIPAY_REFUND_ERROR, response.content if response else e.message)
    else:
        LOGGER.debug(response.content)
        result = parse_xml(response.content)
        if result.is_success == ALIPAY_REFUND_RESPONSE_SUCCESS_MARK:
            LOGGER.info('request alipay refund success: %(params)s', {'params': batch_no})
            return batch_no
        elif result.is_success == ALIPAY_REFUND_RESPONSE_FAIL_MARK:
            if result.error == ALIPAY_REFUND_DUPLICATE_BATCH_NO:
                LOGGER.info('batch_no is duplicate: %(params)s', {'params': params})
                return batch_no
            else:
                LOGGER.error('request alipay refund got failed result: %(error)s, %(params)s, %(response)s',
                             {'error': result.error, 'params': params, 'response': response.content})
                raise ALIPayRefundException(result.error)
        elif result.is_success == ALIPAY_REFUND_RESPONSE_PROCESSING_MARK:
            LOGGER.info('request alipay refund is processing: %(params)s, %(response)', {'params': params, 'response': response.content})
            raise ALIPayRefundException(ALIPAY_REQUEST_REFUND_PROCESSING)


def process_refund_notification(arguments):
    """
    alipay refund asynchronous notification handler

    :param arguments: all arguments submitted to notify_url
    :return: success

    publish event
        DictObject(success=False, reason=...) if sign is incorrect or fake notification from alipay or invalid refund results format
        DictObject(batch_no: 退款批次号, success_num: 成功退款数量, refund_results=[DictObject(trade_no=..., amount=..., success=True/False, [reason=CODE]), ...]
    """
    assert arguments.sign_type == 'MD5', 'unknown sign type'
    if not is_sign_correct(arguments):
        LOGGER.error('got refund notification which sign is incorrect: %(arguments)s', {'arguments': arguments})
        return 'sign is incorrect'
    verify_notification_result = validate_notification_from_alipay(arguments.notify_id)
    if verify_notification_result:
        LOGGER.error('got refund notification which is not from alipay: %(arguments)s', {'arguments': arguments})
        return 'fake notification'
    ret_data = DictObject(batch_no=arguments.batch_no)
    refund_result = arguments.result_details
    try:
        trade_no, amount, result_code = refund_result.split('^')
    except Exception:
        LOGGER.error('got refund notification which refund result format is unexpected: %(result)s', {'result': refund_result})
        return 'invalid refund results format'
    else:
        ret_data.trade_no = trade_no
        ret_data.amount = Decimal(amount)
        if result_code == ALIPAY_REFUND_RESULT_SUCCESS_MARK:
            ret_data.success = True
        else:
            ret_data.success = False
            ret_data.reason = result_code
    publish_event(EVENT_ALIPAY_REFUND_NOTIFIED, result=ret_data)
    return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


def process_dback_notification(arguments):
    """
    alipay dback notification handler

    :param arguments: all arguments submitted to notify_url
    :return: success

    publish event
        DictObject(success=False, reason=...) if sign is incorrect or fake notification from alipay
        DictObject(trade_no: 原支付交易号, refund_id: 退款id, refund_batch_no: 退款批次号, refund_to_card_no: 退还到的银行卡号或支付宝账户,
            refund_to_bank_name=退还到的银行或支付宝, success=True/False [, reason=...])
    """
    if not is_sign_correct(arguments):
        LOGGER.error('got dback notification which sign is incorrect: %(arguments)s', {'arguments': arguments})
        return 'sign is incorrect'
    verify_notification_result = validate_notification_from_alipay(arguments.notify_id)
    if verify_notification_result:
        LOGGER.error('got dback notification which is not from alipay: %(arguments)s', {'arguments': arguments})
        return 'fake notification'
    result = DictObject(trade_no=arguments.trade_no, refund_id=arguments.refund_id, refund_batch_no=arguments.refund_batch_no,
                        refund_to_card_no=arguments.card_no, refund_to_bank_name=arguments.bank_name,
                        success=arguments.status == ALIPAY_DBACK_RESULT_SUCCESS_MARK)
    if arguments.status in (ALIPAY_DBACK_RESULT_WAITING_MARK, ALIPAY_DBACK_RESULT_FAIL_MARK):
        result.reason = '退还至原支付卡失败，在用户余额中'
    publish_event(EVENT_ALIPAY_DBACK_NOTIFIED, result=result)
    return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


class ALIPayRefundException(Exception):
    def __init__(self, code, reason=''):
        super(ALIPayRefundException, self).__init__(code, reason)
        self.code = code
        self.reason = reason

    @property
    def is_timeout(self):
        return self.code == ALIPAY_REFUND_TIMEOUT

    @property
    def is_processing(self):
        return self.code in {ALIPAY_REQUEST_REFUND_PROCESSING, ALIPAY_REFUND_PROCESSING, ALIPAY_REFUND_INIT}

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, reason: {}'.format(self.code, self.reason)

    def __str__(self):
        return self.__unicode__().encode('utf-8')
