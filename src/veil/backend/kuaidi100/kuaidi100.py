# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from time import sleep

from datetime import datetime

from veil.model.collection import objectify, DictObject
from veil.utility.clock import *
from veil.utility.http import *
from .kuaidi100_client_installer import kuaidi100_client_config

LOGGER = logging.getLogger(__name__)

API_URL = 'https://api.kuaidi100.com/api'
WEB_URL_TEMPLATE = 'https://www.kuaidi100.com/chaxun?com={}&nu={}'

STATUS_NO_INFO_YET = '0'  # 物流单暂无结果
STATUS_QUERY_SUCCESS = '1'  # 查询成功
STATUS_QUERY_ERROR = '2'  # 接口出现异常

DELIVERY_STATE_DELIVERING = '0'  # 在途中
DELIVERY_STATE_SHIPPED = '1'  # 已发货
DELIVERY_STATE_PROBLEM = '2'  # 疑难件
DELIVERY_STATE_SIGNED = '3'  # 已签收
DELIVERY_STATE_REJECTED = '4'  # 已退货，即拒收


def waybill_web_url(shipper_code, shipping_code):
    return WEB_URL_TEMPLATE.format(shipper_code, shipping_code)


def get_delivery_status_by_kuaidi100(shipper_code, shipping_code, sleep_at_start=0):
    """
    @param shipper_code: kuaidi100 shipping provider code
    @param shipping_code: trace code
    @param sleep_at_start: back log time
    @return: empty object if got error, {signed:=BOOLEAN, rejected:=BOOLEAN, traces:=[{text:=STRING}]}
    """
    params = {'id': kuaidi100_client_config().api_id, 'com': shipper_code, 'nu': shipping_code, 'muti': '1', 'order': 'desc'}
    # sleep_at_start: avoid IP blocking due to too frequent queries
    if sleep_at_start > 0:
        sleep(sleep_at_start)
    try:
        response = requests.get(API_URL, params=params, headers={'Accept': 'application/json'}, timeout=(3.05, 9),
                                max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('kuaidi100 query exception-thrown: %(params)s', {'params': params})
    else:
        result = objectify(response.json())
        if result.status == STATUS_QUERY_SUCCESS:
            LOGGER.debug('kuaidi100 query succeeded: %(result)s, %(url)s', {'result': result, 'url': response.url})
            ret = DictObject(signed=result.state == DELIVERY_STATE_SIGNED, rejected=result.state == DELIVERY_STATE_REJECTED)
            ret.traces = [DictObject(text=trace.context) for trace in result.data]
            if result.data[0].time:
                ret.delivered_at = convert_datetime_to_utc_timezone(datetime.strptime(result.data[0].time, '%Y-%m-%d %H:%M:%S'))
            else:
                ret.delivered_at = get_current_time()
            return ret
        elif result.status == STATUS_QUERY_ERROR:
            LOGGER.error('kuaidi100 query error: %(result)s, %(url)s', {'result': result, 'url': response.url})
        elif result.status == STATUS_NO_INFO_YET:
            if all(keyword in result.message for keyword in ('IP地址', '禁止')):
                raise IPBlockedException('IP blocked by kuaidi100: {}'.format(result))
            else:
                LOGGER.info('kuaidi100 query no info yet: %(result)s, %(url)s', {'result': result, 'url': response.url})
    return {}


class IPBlockedException(Exception):
    pass
