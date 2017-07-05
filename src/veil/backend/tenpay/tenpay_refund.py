# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import hashlib
import logging
from decimal import Decimal

from veil.profile.model import *
from veil.utility.http import *
from .tenpay_client_installer import tenpay_client_config
from .tenpay_payment import sign_md5, parse_xml_response, is_sign_correct, NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK

LOGGER = logging.getLogger(__name__)

EVENT_TENPAY_REFUND_NOTIFIED = define_event('tenpay-refund-notified')

REFUND_URL = 'https://api.mch.tenpay.com/refundapi/gateway/refund.xml'
REFUND_QUERY_URL = 'https://gw.tenpay.com/gateway/normalrefundquery.xml'

TENPAY_REFUND_ERROR_CODE = '-1'
TENPAY_REFUND_TIMEOUT_CODE = '-2'
TENPAY_REFUND_REQUEST_PROCESSING_CODE = '-3'

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
        LOGGER.exception('request to tenpay refund got read timeout: %(data)s', {'data': data})
        raise TENPayRefundException(TENPAY_REFUND_TIMEOUT_CODE, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('request to tenpay refund got exception: %(data)s, %(response)s', {'data': data, 'response': response.content if response else ''})
        raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, response.content if response else e.message)
    else:
        result = parse_xml_response(response.content)
        assert result.input_charset == 'UTF-8', 'assume tenpay use same input charset as request'
        assert result.sign_type == 'MD5', 'assume tenpay use same sign type as request'
        if not is_sign_correct(result):
            LOGGER.error('request to tenpay refund got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'sign is incorrect')
        if result.retcode != '0':
            LOGGER.error('request to tenpay refund got failed response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise TENPayRefundException(result.retcode, result.retmsg)

        reasons = []
        _refund_fee = Decimal(result.refund_fee) / 100
        if result.partner != partner_id:
            reasons.append('partner mismatch, _partner_id: {}, partner_id: {}'.format(result.partner, partner_id))
        elif result.out_trade_no != out_trade_no:
            reasons.append('out trade no mismatch, _out_trade_no: {}, out_trade_no: {}'.format(result.out_trade_no, out_trade_no))
        elif result.out_refund_no != out_refund_no:
            reasons.append('out refund no mismatch, _out_refund_no: {}, out_refund_no: {}'.format(result.out_refund_no, out_refund_no))
        elif _refund_fee != refund_fee:
            reasons.append('refund fee mismatch, tenpay refund fee: {}, request refund fee: {}'.format(_refund_fee, refund_fee))
        if reasons:
            LOGGER.error('request to tenpay refund got invalid response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, '；'.join(reasons))

        if result.refund_status in TENPAY_REFUND_STATUS_NEED_RETRY_MARKS:
            LOGGER.error('request to tenpay refund got need retry response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_REQUEST_PROCESSING_CODE, '请重试')

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
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'unknown refund status:{}'.format(result.refund_status))
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
        raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'sign is incorrect')
    if arguments.partner != tenpay_client_config().partner_id:
        raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'partner id mismatch, _partner_id: {}, partner_id: {}'.format(arguments.partner,
                                                                                                                            tenpay_client_config().partner_id))
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
        raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'unknown refund status:{}'.format(arguments.refund_status))
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
        raise TENPayRefundException(TENPAY_REFUND_TIMEOUT_CODE, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('query tenpay refund status got exception: %(params)s, %(response)s', {
            'params': params,
            'response': response.content if response else ''
        })
        raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, response.content if response else e.message)
    else:
        result = parse_xml_response(response.content)
        assert result.input_charset == 'UTF-8', 'assume tenpay use same input charset as request'
        assert result.sign_type == 'MD5', 'assume tenpay use same sign type as request'
        if not is_sign_correct(result):
            LOGGER.error('query tenpay refund status got fake response: %(params)s, %(response)s', {'params': params, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'sign is incorrect')
        if result.retcode != '0':
            if result.retcode == '88222014':
                raise TENPayRefundException(result.retcode, '退款失败：订单未退款')
            if result.retcode == '88221009':
                raise TENPayRefundException(result.retcode, '退款失败：订单不存在')
            LOGGER.error('query tenpay refund status got failed response: %(params)s, %(response)s', {'params': params, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, result.retmsg)
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


class TENPayRefundException(Exception):
    def __init__(self, code, reason):
        super(TENPayRefundException, self).__init__(code, reason)
        self.code = code
        self.reason = reason

    @property
    def is_timeout(self):
        return self.code == TENPAY_REFUND_TIMEOUT_CODE

    @property
    def is_processing(self):
        return self.code in {TENPAY_REFUND_REQUEST_PROCESSING_CODE, }

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, reason: {}'.format(self.code, self.reason)

    def __str__(self):
        return self.__unicode__().encode('utf-8')
