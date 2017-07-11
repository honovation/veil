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
TENPAY_REFUND_ERROR_TIMEOUT_CODE = '-2'
TENPAY_REFUND_ERROR_FAILED_CODE = '-3'
TENPAY_REFUND_ERROR_MANUAL_CODE = '-4'

TENPAY_REFUND_ERROR_NOT_EXIST_CODE = '88222014'  # 原交易未退款
TENPAY_REFUND_ERROR_TRADE_NOT_EXIST_CODE = '88221009'  # 原交易不存在

TENPAY_REFUND_STATUS_SUCCESS_MARKS = {'4', '10'}
TENPAY_REFUND_STATUS_FAIL_MARKS = {'3', '5', '6'}  # 更换退款请求号重试
TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK = '9'
TENPAY_REFUND_STATUS_PROCESSING_MARKS = {'8', TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK, '11'}
TENPAY_REFUND_STATUS_UNKNOWN_MARKS = {'1', '2'}
TENPAY_REFUND_STATUS_MANUAL = '7'  # 原路退款至银行卡失败, 需人工处理

TENPAY_REFUND_CHANNEL_TENPAY = '0'
TENPAY_REFUND_CHANNEL_BANK = '1'
TENPAY_REFUND_CHANNELS = {
    TENPAY_REFUND_CHANNEL_TENPAY: '退到财付通',
    TENPAY_REFUND_CHANNEL_BANK: '退到银行'
}


def refund(out_refund_no, out_trade_no, total_fee, refund_fee, notify_url=None):
    """
    tenpay refund

    :param out_refund_no: 外部退款请求号
    :param out_trade_no: 原交易外部订单号
    :param total_fee: 原交易金额, Decimal
    :param refund_fee: 退款金额, Decimal
    :param notify_url: 异步通知URL
    :return:
        DictObject(success=True/False, processing=True/False, failed=True/False, need_retry=True（需更换退款请求号重新发起退款）/False,
            need_handle_manually=True（转入代发，需人工退款）/False, out_trade_no: 原交易外部订单号, out_refund_no: 外部退款请求号, refund_id: 退款id,
            refund_status_text:退款状态（成功/失败/处理中/需人工处理）, refund_fee: 退款金额, refund_channel_text: 退款去向（财付通/银行卡）,
            recv_user_id: 接收退款的财付通账号, reccv_user_name: 接收退款的姓名)
    """
    out_refund_no = unicode(out_refund_no)
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
        response = requests.post(REFUND_URL, data=data, verify=config.api_ca_cert, cert=(config.api_client_cert, config.api_client_key),
                                 timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('request to tenpay refund got read timeout: %(data)s', {'data': data})
        raise TENPayRefundException(TENPAY_REFUND_ERROR_TIMEOUT_CODE, 'read response but timeout')
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
            if result.retcode == TENPAY_REFUND_ERROR_TRADE_NOT_EXIST_CODE:
                raise TENPayRefundException(result.retcode, '退款失败：原交易不存在')
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

        need_retry = result.refund_status in TENPAY_REFUND_STATUS_FAIL_MARKS
        need_handle_manually = result.refund_status == TENPAY_REFUND_STATUS_MANUAL
        ret_data = DictObject(success=result.refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS,
                              processing=result.refund_status in TENPAY_REFUND_STATUS_PROCESSING_MARKS,
                              failed=result.refund_status in TENPAY_REFUND_STATUS_UNKNOWN_MARKS or need_retry or need_handle_manually,
                              need_retry=need_retry,
                              need_handle_manually=need_handle_manually,
                              out_trade_no=out_trade_no,
                              out_refund_no=out_refund_no,
                              refund_id=result.refund_id,
                              refund_fee=refund_fee,
                              refund_channel_text=TENPAY_REFUND_CHANNELS[result.refund_channel],
                              recv_user_id=result.get('recv_user_id'),
                              reccv_user_name=result.get('reccv_user_name'))
        if ret_data.success:
            ret_data.refund_status_text = '退款成功'
        elif ret_data.processing:
            ret_data.refund_status_text = '退款处理中'
            if result.refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
                ret_data.refund_status_text = '退款处理中：已提交退款请求给银行'
        elif ret_data.failed:
            if ret_data.need_retry:
                ret_data.refund_status_text = '退款失败：请更换退款请求号重新发起退款'
            elif ret_data.need_handle_manually:
                ret_data.refund_status_text = '退款失败：转入代发，需人工退款'
            else:
                ret_data.refund_status_text = '状态未确定：使用原退款请求号重新发起退款'
        else:
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'unknown refund status:{}'.format(result.refund_status))
        return ret_data


def process_refund_notification(arguments):
    """
    tenpay refund asynchronous notification handler

    只有退款成功/需人工处理/已提交请求给银行 (状态码为：4, 7, 9 ,10) 才可以收到通知

    :param arguments: all arguments submitted to notify_url
    :return:
        success / fail
        publish event if success, arguments are same as refund
    """
    if not is_sign_correct(arguments):
        return 'sign is incorrect'
    if arguments.partner != tenpay_client_config().partner_id:
        return 'partner id mismatch'
    if arguments.refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
        return 'tenpay refund is processing'
    ret_data = DictObject(
        sucesss=arguments.refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS,
        failed=arguments.refund_status == TENPAY_REFUND_STATUS_MANUAL,
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
        ret_data.refund_status_text = '退款失败：转入代发，需人工退款'
    else:
        return 'unknown refund status:{}'.format(arguments.refund_status)
    publish_event(EVENT_TENPAY_REFUND_NOTIFIED, refund_result=ret_data)
    return NOTIFICATION_RECEIVED_SUCCESSFULLY_MARK


def query_refund_status(out_refund_no):
    """
    query refund status

    :param out_refund_no: 退款请求号
    :return:
        DictObject(refund_status=[DictObject(success=True/False, processing=True/False, failed=True/False, need_retry=True（需更换退款请求号重新发起退款）/False,
            need_handle_manually=True（转入代发，需人工退款）/False, out_trade_no: 原交易外部订单号, out_refund_no: 外部退款请求号,
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
        raise TENPayRefundException(TENPAY_REFUND_ERROR_TIMEOUT_CODE, 'read response but timeout')
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
            LOGGER.error('query tenpay refund status got failed response: %(params)s, %(response)s', {'params': params, 'response': response.content})
            if result.retcode == TENPAY_REFUND_ERROR_NOT_EXIST_CODE:
                raise TENPayRefundException(result.retcode, '退款失败：原交易未退款')
            if result.retcode == TENPAY_REFUND_ERROR_TRADE_NOT_EXIST_CODE:
                raise TENPayRefundException(result.retcode, '退款失败：原交易不存在')
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, result.retmsg)

        _refund_status = result.get('refund_state_0')
        success = _refund_status in TENPAY_REFUND_STATUS_SUCCESS_MARKS
        processing = _refund_status in TENPAY_REFUND_STATUS_PROCESSING_MARKS | TENPAY_REFUND_STATUS_UNKNOWN_MARKS
        need_retry = _refund_status in TENPAY_REFUND_STATUS_FAIL_MARKS
        need_handle_manually = _refund_status == TENPAY_REFUND_STATUS_MANUAL
        failed = _refund_status in TENPAY_REFUND_STATUS_UNKNOWN_MARKS or need_retry or need_handle_manually
        if success:
            refund_status_text = '退款成功'
        elif processing:
            refund_status_text = '退款处理中'
            if _refund_status == TENPAY_REFUND_STATUS_PROCESSING_SUBMITTED_TO_BANK:
                refund_status_text = '退款处理中：已提交退款请求给银行'
        elif failed:
            if need_retry:
                refund_status_text = '退款失败：请更换退款请求号重新发起退款'
            elif need_handle_manually:
                refund_status_text = '退款失败：转入代发，需人工退款'
            else:
                refund_status_text = '状态未确定：使用原退款请求号重新发起退款'
        else:
            LOGGER.error('query tenpay refund status got unknown status: %(params)s, %(response)s', {'params': params, 'response': response.content})
            raise TENPayRefundException(TENPAY_REFUND_ERROR_CODE, 'unknown refund status')

        refund_time_begin = result.get('refund_time_begin_0')
        if refund_time_begin:
            refund_time_begin = to_datetime(format='%Y%m%d%H%M%S')(refund_time_begin)
        refund_time_last_modify = result.get('refund_time_0')
        if refund_time_last_modify:
            refund_time_last_modify = to_datetime(format='%Y%m%d%H%M%S')(refund_time_last_modify)
        return DictObject(
            success=success,
            processing=processing,
            failed=failed,
            need_retry=need_retry,
            need_handle_manually=need_handle_manually,
            refund_status_text=refund_status_text,
            out_trade_no=result.out_trade_no,
            out_refund_no=result.get('out_refund_no_0'),
            refund_id=result.get('refund_id_0'),
            refund_fee=Decimal(result.get('refund_fee_0')) / 100,
            refund_channel_text=TENPAY_REFUND_CHANNELS[result.get('refund_channel_0')],
            recv_user_id=result.get('recv_user_id_0'),
            reccv_user_name=result.get('reccv_user_name_0'),
            refund_time_begin=refund_time_begin,
            refund_time_last_modify=refund_time_last_modify
        )


class TENPayRefundException(Exception):
    def __init__(self, code, reason):
        super(TENPayRefundException, self).__init__(code, reason)
        self.code = code
        self.reason = reason

    @property
    def is_not_exist(self):
        return self.code == TENPAY_REFUND_ERROR_NOT_EXIST_CODE

    @property
    def is_trade_not_exist(self):
        return self.code == TENPAY_REFUND_ERROR_TRADE_NOT_EXIST_CODE

    @property
    def is_timeout(self):
        return self.code == TENPAY_REFUND_ERROR_TIMEOUT_CODE

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, reason: {}'.format(self.code, self.reason)

    def __str__(self):
        return self.__unicode__().encode('utf-8')
