# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import json
import logging

import requests

from veil.profile.model import *
from veil.utility.http import Retry
from .alipay_client_installer import alipay_client_config
from .alipay_payment import sign_rsa2, ALIPAY_API_URL, REQUEST_SUCCESS_CODE, validate_query_return_arguments

LOGGER = logging.getLogger(__name__)

REFUND_ERROR_CODE = '100000'


def refund(out_refund_no, out_trade_no, refund_amount, refund_reason):
    """
    request alipay refund

    :param out_refund_no: 外部退款单号
    :param out_trade_no: 原交易外部订单号
    :param refund_amount: 退款金额, Decimal
    :param refund_reason: 退款原因
    :return:
        DictObject(out_refund_no: 商户退款单号, out_trade_no: 原交易外部订单号, buyer_id: 支付宝账号（如：15901825620）, refund_amount: 申请退款金额)
    """
    config = alipay_client_config()
    refund_amount = '{:.2f}'.format(refund_amount)
    content_params = DictObject(out_request_no=out_refund_no, out_trade_no=out_trade_no, refund_amount=refund_amount, refund_reason=refund_reason)
    params = DictObject(
        app_id=config.app_id,
        method='alipay.trade.refund',
        charset='utf-8',
        timestamp=get_current_time_in_client_timezone().strftime('%Y-%m-%d %H:%M:%S'),
        biz_content=json.dumps(content_params, separators=(',', ':')),
        version='1.0',
        sign_type='RSA2'
    )
    params.sign = sign_rsa2(params, config.rsa2_private_key)
    try:
        response = requests.get(ALIPAY_API_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('request to refund alipay get exception: %(params)s', {'params': params})
        raise
    else:
        LOGGER.debug(response.content)
        content = from_json(response.content)
        arguments = DictObject(content['alipay_trade_refund_response'])
        arguments.sign = content['sign']
        if arguments.code == REQUEST_SUCCESS_CODE:
            if not validate_query_return_arguments(arguments):
                LOGGER.error('verify alipay refund return arguments failed: %(out_refund_no)s, %(arguments)s',
                             {'out_refund_no': out_refund_no, 'arguments': arguments})
                return

            if arguments['out_trade_no'] != out_trade_no:
                raise ALIPayRefundException(REFUND_ERROR_CODE, 'out trade no mismatch')

            LOGGER.info('request to refund alipay successfully: %(out_refund_no)s, %(params)s, %(arguments)s',
                        {'out_refund_no': out_refund_no, 'params': params, 'arguments': arguments})
            return DictObject(out_refund_no=out_refund_no, out_trade_no=out_trade_no, buyer_id=arguments.buyer_logon_id, refund_amount=arguments.refund_fee)
        else:
            LOGGER.error('request to refund alipay failed: %(out_refund_no)s, %(code)s, %(msg)s, %(sub_code)s, %(sub_msg)s, %(params)s, %(arguments)s',
                         {'out_refund_no': out_refund_no, 'code': arguments.code, 'msg': arguments.msg, 'sub_code': arguments.sub_code,
                          'sub_msg': arguments.sub_msg, 'params': params, 'arguments': arguments})
            raise ALIPayRefundException(arguments.code, arguments.msg, arguments.sub_code, arguments.sub_msg)


def query_refund_status(out_refund_no, out_trade_no):
    """
    query alipay refund status

    :param out_refund_no: 外部退款单号
    :param out_trade_no: 原交易外部订单号
    :return:
        DictObject(success: True/False（退款完成/退款中）, out_refund_no: 商户退款单号, out_trade_no: 原交易外部订单号, refund_amount: 申请退款金额,
            refund_reason: 退款原因)
    """
    config = alipay_client_config()
    content_params = DictObject(out_request_no=out_refund_no, out_trade_no=out_trade_no)
    params = DictObject(
        app_id=config.app_id,
        method='alipay.trade.fastpay.refund.query',
        charset='utf-8',
        timestamp=get_current_time_in_client_timezone().strftime('%Y-%m-%d %H:%M:%S'),
        biz_content=json.dumps(content_params, separators=(',', ':')),
        version='1.0',
        sign_type='RSA2'
    )
    params.sign = sign_rsa2(params, config.rsa2_private_key)
    try:
        response = requests.get(ALIPAY_API_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('request to alipay refund get exception: %(params)s', {'params': params})
        raise
    else:
        LOGGER.debug(response.content)
        content = from_json(response.content)
        arguments = DictObject(content['alipay_trade_fastpay_refund_query_response'])
        arguments.sign = content['sign']
        if arguments.code == REQUEST_SUCCESS_CODE:
            if not validate_query_return_arguments(arguments):
                LOGGER.error('verify alipay refund query return arguments failed: %(out_refund_no)s, %(arguments)s',
                             {'out_refund_no': out_refund_no, 'arguments': arguments})
                return

            LOGGER.info('query alipay refund status successfully: %(out_refund_no)s, %(params)s, %(arguments)s',
                        {'out_refund_no': out_refund_no, 'params': params, 'arguments': arguments})
            success = bool(arguments.get('out_request_no'))
            return DictObject(success=success, out_refund_no=out_refund_no, out_trade_no=out_trade_no, refund_amount=arguments.get('refund_amount'),
                              refund_reason=arguments.get('refund_reason'))
        else:
            LOGGER.error('query alipay refund status failed: %(out_refund_no)s, %(code)s, %(msg)s, %(sub_code)s, %(sub_msg)s, %(params)s, %(arguments)s',
                         {'out_refund_no': out_refund_no, 'code': arguments.code, 'msg': arguments.msg, 'sub_code': arguments.sub_code,
                          'sub_msg': arguments.sub_msg, 'params': params, 'arguments': arguments})
            raise ALIPayRefundException(arguments.code, arguments.msg, arguments.sub_code, arguments.sub_msg)


class ALIPayRefundException(Exception):
    def __init__(self, code, msg, sub_code=None, sub_msg=None):
        super(ALIPayRefundException, self).__init__(code, msg, sub_code, sub_msg)
        self.code = code
        self.msg = msg
        self.sub_code = sub_code
        self.sub_msg = sub_msg

    @property
    def is_temporarily_unavailable(self):
        return self.code == '20000' or self.sub_code == 'ACQ.SYSTEM_ERROR'  # 服务暂时不可用 / 系统错误，需重试

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, msg: {}, sub_code: {}, sub_msg: {}'.format(self.code, self.msg, self.sub_code or '', self.sub_msg or '')

    def __str__(self):
        return self.__unicode__().encode('utf-8')
