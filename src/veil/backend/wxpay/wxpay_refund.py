# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import logging
from decimal import Decimal
from uuid import uuid4

from veil.frontend.template import *
from veil.profile.model import *
from veil.utility.http import *
from .wxpay_client_installer import wxpay_client_config
from .wxpay_payment import sign_md5, parse_xml_response, SUCCESSFULLY_MARK, verify_wxpay_response

LOGGER = logging.getLogger(__name__)

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

SYSTEMERROR_MARK = 'SYSTEMERROR'

WXPAY_REFUND_STATUS_SUCCESS = 'SUCCESS'
WXPAY_REFUND_STATUS_CLOSED = 'REFUNDCLOSE'
WXPAY_REFUND_STATUS_PROCESSING = 'PROCESSING'
WXPAY_REFUND_STATUS_CHANGE = 'CHANGE'
WXPAY_REFUND_STATUS = {
    WXPAY_REFUND_STATUS_SUCCESS: '退款成功',
    WXPAY_REFUND_STATUS_PROCESSING: '退款处理中',
    WXPAY_REFUND_STATUS_CHANGE: '转入代发，需人工退款'
}


def refund(out_refund_no, out_trade_no, total_fee, refund_fee):
    """
    request to wxpay refund

    :param out_refund_no: 外部退款单号
    :param out_trade_no: 原交易外部订单号
    :param total_fee: 原交易金额, Decimal
    :param refund_fee: 退款金额, Decimal
    :return:
        DictObject(out_refund_no: 商户退款单号, refund_id: 退款id, out_trade_no: 原交易外部订单号, refund_channel_text: 退款去向（原支付卡/余额）,
            refund_fee: 申请退款金额, settlement_refund_fee: 扣除非充值的代金券后实际退款金额（APP微信退款接口无该字段，这里保留该字段，值与refund_fee一致）)
    """
    if refund_fee > total_fee:
        raise WXPayRefundException(WXPAY_REFUND_ERROR, 'refund_fee can not be greater than total_fee')

    config = wxpay_client_config()
    refund_request = DictObject(appid=config.app_id, mch_id=config.mch_id, nonce_str=uuid4().get_hex(), out_refund_no=str(out_refund_no),
                                out_trade_no=out_trade_no, total_fee=unicode(int(total_fee * 100)), refund_fee=unicode(int(refund_fee * 100)),
                                op_user_id=config.mch_id)
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
        LOGGER.exception('request to wxpay refund got read timeout: %(data)s', {'data': data})
        raise WXPayRefundException(WXPAY_REFUND_TIMEOUT, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('request to wxpay refund got exception: %(out_refund_no)s, %(data)s, %(response)s', {
            'out_refund_no': out_refund_no,
            'data': data,
            'response': response.content if response else e.message
        })
        raise WXPayRefundException(WXPAY_REFUND_ERROR, response.content if response else e.message)
    else:
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.error('request to wxpay refund got failed response: %(out_refund_no)s, %(return_msg)s, %(data)s',
                         {'out_refund_no': out_refund_no, 'return_msg': parsed_response.return_msg, 'data': data})
            raise WXPayRefundException(WXPAY_REFUND_ERROR, parsed_response.return_msg)
        try:
            verify_wxpay_response(parsed_response, config.api_key)
        except Exception:
            LOGGER.error('request to wxpay refund got fake response: %(out_refund_no)s, %(data)s, %(response)s',
                         {'out_refund_no': out_refund_no, 'data': data, 'response': response.content})
            raise WXPayRefundException(WXPAY_REFUND_ERROR, 'sign is incorrect')

        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.error('request to wxpay refund got failed result: %(out_refund_no)s, %(err_code)s, %(err_code_des)s, %(data)s, %(response)s', {
                'out_refund_no': out_refund_no,
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data,
                'response': response.content
            })
            raise WXPayRefundException(parsed_response.result_code, parsed_response.err_code_des)

        reasons = []
        if parsed_response.out_trade_no != out_trade_no:
            reasons.append('out trade no mismatch, _out_trade_no: {}, out_trade_no: {}'.format(parsed_response.out_trade_no, out_trade_no))
        if parsed_response.out_refund_no != out_refund_no:
            reasons.append('out refund no mismatch, _out_refund_no: {}, out_refund_no: {}'.format(parsed_response.out_refund_no, out_refund_no))
        _refund_fee = Decimal(parsed_response.refund_fee) / 100
        if _refund_fee != refund_fee:
            reasons.append('refund fee mismatch, wxpay refund fee: {}, request refund fee: {}'.format(_refund_fee, refund_fee))
        if reasons:
            LOGGER.error('request to wxpay refund got invalid response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise WXPayRefundException(WXPAY_REFUND_ERROR, '；'.join(reasons))

        settlement_refund_fee = parsed_response.get('settlement_refund_fee')
        if settlement_refund_fee:
            settlement_refund_fee = Decimal(settlement_refund_fee) / 100
        else:
            settlement_refund_fee = _refund_fee
        refund_channel_text = None
        refund_channel = parsed_response.get('refund_channel')
        if refund_channel:
            refund_channel_text = WXPAY_REFUND_CHANNELS[refund_channel]
        LOGGER.info('request to wxpay refund success: %(out_refund_no)s, %(data)s, %(response)s',
                    {'out_refund_no': out_refund_no, 'data': data, 'response': response.content})
        return DictObject(out_refund_no=parsed_response.out_refund_no, refund_id=parsed_response.refund_id, out_trade_no=parsed_response.out_trade_no,
                          refund_channel_text=refund_channel_text, refund_fee=_refund_fee, settlement_refund_fee=settlement_refund_fee)


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
        raise WXPayRefundException(WXPAY_REFUND_TIMEOUT, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('query wxpay refund status got exception: %(out_refund_no)s, %(data)s, %(response)s', {
            'out_refund_no': out_refund_no,
            'data': data,
            'response': response.content if response else ''
        })
        raise WXPayRefundException(WXPAY_REFUND_ERROR, 'read response but timeout')
    else:
        LOGGER.debug(response.content)
        parsed_response = parse_xml_response(response.content)
        if parsed_response.return_code != SUCCESSFULLY_MARK:
            LOGGER.error('query wxpay refund status got failed response: %(return_msg)s, %(data)s', {'return_msg': parsed_response.return_msg, 'data': data})
            raise WXPayRefundException(WXPAY_REFUND_ERROR, parsed_response.return_msg)
        try:
            verify_wxpay_response(parsed_response, config.api_key)
        except Exception:
            LOGGER.error('query wxpay refund status got fake response: %(data)s, %(response)s', {'data': data, 'response': response.content})
            raise WXPayRefundException(WXPAY_REFUND_ERROR, 'sign is incorrect')

        if parsed_response.result_code != SUCCESSFULLY_MARK:
            LOGGER.error('query wxpay refund status got failed result: %(err_code)s, %(err_code_des)s, %(data)s, %(response)s', {
                'err_code': parsed_response.err_code,
                'err_code_des': parsed_response.err_code_des,
                'data': data,
                'response': response.content
            })
            raise WXPayRefundException(WXPAY_REFUND_ERROR, parsed_response.err_code_des)

        LOGGER.info('query wxpay refund status success: %(data)s, %(response)s', {'data': data, 'response': response.content})
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


class WXPayRefundException(Exception):
    def __init__(self, code, reason):
        super(WXPayRefundException, self).__init__(code, reason)
        self.code = code
        self.reason = reason

    @property
    def is_timeout(self):
        return self.code in {WXPAY_REFUND_TIMEOUT, SYSTEMERROR_MARK}  # 处理超时

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, reason: {}'.format(self.code, self.reason)

    def __str__(self):
        return self.__unicode__().encode('utf-8')
