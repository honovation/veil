# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import json
import logging
from decimal import Decimal

from veil.profile.model import *
from veil.utility.http import *
from .alipay_client_installer import alipay_client_config
from .alipay_payment import sign_rsa2, ALIPAY_API_URL, REQUEST_SUCCESS_CODE, validate_query_return_arguments

LOGGER = logging.getLogger(__name__)

REFUND_ERROR_CODE = '-1'
REFUND_TIMEOUT_CODE = '-2'


def refund(out_refund_no, out_trade_no, refund_amount, refund_reason):
    """
    request alipay refund

    :param out_refund_no: 外部退款单号
    :param out_trade_no: 原交易外部订单号
    :param refund_amount: 退款金额, Decimal
    :param refund_reason: 退款原因
    :return:
        DictObject(out_refund_no: 商户退款单号, out_trade_no: 原交易外部订单号, buyer_id: 支付宝账号（如：15901825620）, refund_total_amount: 退款总金额)
    """
    out_refund_no = unicode(out_refund_no)
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
    response = None
    try:
        response = requests.get(ALIPAY_API_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('request to alipay refund got read timeout: %(params)s', {'params': params})
        raise ALIPayRefundException(REFUND_TIMEOUT_CODE, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('request to alipay refund get exception: %(params)s', {'params': params})
        raise ALIPayRefundException(REFUND_ERROR_CODE, response.content if response else e.message)
    else:
        LOGGER.debug(response.content)
        content = from_json(response.content)
        arguments = DictObject(content['alipay_trade_refund_response'])
        arguments.sign = content['sign']

        if arguments.code == REQUEST_SUCCESS_CODE:
            if not validate_query_return_arguments(arguments):
                LOGGER.error('verify alipay refund return arguments failed: %(out_refund_no)s, %(arguments)s',
                             {'out_refund_no': out_refund_no, 'arguments': arguments})
                raise ALIPayRefundException(REFUND_ERROR_CODE, 'sign is incorrect')

            if arguments.out_trade_no != out_trade_no:
                LOGGER.error('request to alipay refund got invalid response: %(params)s, %(response)s', {'params': params, 'response': response.content})
                raise ALIPayRefundException(REFUND_ERROR_CODE, 'out trade no mismatch, _out_trade_no: {}, out_trade_no: {}'.format(arguments.out_trade_no,
                                                                                                                                   out_trade_no))

            LOGGER.info('request to alipay refund successfully: %(out_refund_no)s, %(params)s, %(arguments)s',
                        {'out_refund_no': out_refund_no, 'params': params, 'arguments': arguments})
            return DictObject(out_refund_no=out_refund_no, out_trade_no=out_trade_no, buyer_id=arguments.buyer_logon_id,
                              refund_total_amount=Decimal(arguments.refund_fee))
        else:
            LOGGER.error('request to alipay refund failed: %(out_refund_no)s, %(code)s, %(msg)s, %(sub_code)s, %(sub_msg)s, %(params)s, %(arguments)s',
                         {'out_refund_no': out_refund_no, 'code': arguments.code, 'msg': arguments.msg, 'sub_code': arguments.sub_code,
                          'sub_msg': arguments.sub_msg, 'params': params, 'arguments': arguments})
            raise ALIPayRefundException(arguments.code, arguments.msg, arguments.sub_code, arguments.sub_msg)


def query_refund_status(out_refund_no, out_trade_no):
    """
    query alipay refund status

    :param out_refund_no: 外部退款单号
    :param out_trade_no: 原交易外部订单号
    :return:
        DictObject(
                success: True/False（退款完成/退款中）,
                data: DictObject(out_refund_no: 商户退款单号, out_trade_no: 原交易外部订单号, refund_amount: 申请退款金额, refund_reason: 退款原因)
                )
    """
    out_refund_no = unicode(out_refund_no)
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
    response = None
    try:
        response = requests.get(ALIPAY_API_URL, params=params, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.2))
        response.raise_for_status()
    except ReadTimeout:
        LOGGER.exception('query alipay refund status got read timeout: %(params)s', {'params': params})
        raise ALIPayRefundException(REFUND_TIMEOUT_CODE, 'read response but timeout')
    except Exception as e:
        LOGGER.exception('query alipay refund status get exception: %(params)s', {'params': params})
        raise ALIPayRefundException(REFUND_ERROR_CODE, response.content if response else e.message)
    else:
        LOGGER.debug(response.content)
        content = from_json(response.content)
        arguments = DictObject(content['alipay_trade_fastpay_refund_query_response'])
        arguments.sign = content['sign']

        if arguments.code == REQUEST_SUCCESS_CODE:
            if not validate_query_return_arguments(arguments):
                LOGGER.error('verify alipay refund query return arguments failed: %(out_refund_no)s, %(arguments)s',
                             {'out_refund_no': out_refund_no, 'arguments': arguments})
                raise ALIPayRefundException(REFUND_ERROR_CODE, 'sign is incorrect')

            LOGGER.info('query alipay refund status successfully: %(out_refund_no)s, %(params)s, %(arguments)s',
                        {'out_refund_no': out_refund_no, 'params': params, 'arguments': arguments})
            if arguments.get('out_request_no'):
                return DictObject(success=True,
                                  data=DictObject(out_refund_no=out_refund_no, out_trade_no=out_trade_no, refund_amount=Decimal(arguments['refund_amount']),
                                                  refund_reason=arguments.get('refund_reason')))
            else:
                return DictObject(success=False, data=None)
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
    def is_timeout(self):
        return self.code == REFUND_TIMEOUT_CODE

    @property
    def is_temporarily_unavailable(self):
        return self.code == '20000' or self.sub_code == 'ACQ.SYSTEM_ERROR'  # 服务暂时不可用 / 系统错误，需重试

    @property
    def is_not_enough(self):
        return self.sub_code == 'ACQ.SELLER_BALANCE_NOT_ENOUGH'  # 卖家余额不足

    @property
    def is_not_equal_total(self):
        return self.sub_code == 'ACQ.REFUND_AMT_NOT_EQUAL_TOTAL'  # 退款金额超限

    @property
    def is_been_freezen(self):
        return self.sub_code == 'ACQ.REASON_TRADE_BEEN_FREEZEN'  # 退款交易被冻结

    @property
    def is_not_exist(self):
        return self.sub_code == 'ACQ.TRADE_NOT_EXIST'  # 原交易不存在

    @property
    def is_finished(self):
        return self.sub_code == 'ACQ.TRADE_HAS_FINISHED'  # 原交易已完结

    @property
    def is_not_allow_refund(self):
        return self.sub_code == 'ACQ.TRADE_NOT_ALLOW_REFUND'  # 原交易不允许退款

    def __unicode__(self):  # TODO: not necessary under python3
        return 'code: {}, msg: {}, sub_code: {}, sub_msg: {}'.format(self.code, self.msg, self.sub_code or '', self.sub_msg or '')

    def __str__(self):
        return unicode(self).encode(encoding='UTF-8')
