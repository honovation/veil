# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from time import sleep
from veil.model.collection import objectify
from veil.utility.http import *
from .kuaidi100_client_installer import kuaidi100_client_config

LOGGER = logging.getLogger(__name__)

API_URL = 'http://api.kuaidi100.com/api'
WEB_URL_TEMPLATE = 'http://www.kuaidi100.com/chaxun?com={}&nu={}'

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


def get_delivery_status(shipper_code, shipping_code, sleep_at_start=0):
    if 'youzhengguonei' == shipper_code: # kuaidi100 API does not support China Post yet
        return {}
    params = {'id': kuaidi100_client_config().api_id, 'com': shipper_code, 'nu': shipping_code, 'muti': '1', 'order': 'desc'}
    # sleep_at_start: avoid IP blocking due to too frequent queries
    if sleep_at_start > 0:
        sleep(sleep_at_start)
    try:
        response = requests.get(API_URL, params=params, headers={'Accept': 'application/json'}, timeout=(3.05, 9),
            max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except:
        LOGGER.exception('kuaidi100 query exception-thrown: %(params)s', {'params': params})
    else:
        result = objectify(response.json())
        if result.status == STATUS_QUERY_SUCCESS:
            LOGGER.debug('kuaidi100 query succeeded: %(result)s, %(url)s', {'result': result, 'url': response.url})
            return result
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
