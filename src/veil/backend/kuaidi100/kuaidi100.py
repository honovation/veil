# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import urllib
from veil.utility.encoding import *
from veil.utility.http import *
from .kuaidi100_client_installer import kuaidi100_client_config

LOGGER = logging.getLogger(__name__)

WEB_URL_TEMPLATE = 'http://www.kuaidi100.com/chaxun?com={}&nu={}'
API_URL_TEMPLATE = 'http://api.kuaidi100.com/api?id={}&com={}&nu={}&show=0&muti=1&order=desc'

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
    url = API_URL_TEMPLATE.format(kuaidi100_client_config().api_id, shipper_code, urllib.quote(to_str(shipping_code)))
    try:
        # sleep_at_start & sleep_before_retry: avoid IP blocking due to too frequent queries
        response = http_call('KUAIDI100-QUERY-API', url, accept='application/json', max_tries=2, sleep_at_start=sleep_at_start, sleep_before_retry=10)
    except Exception as e:
        pass
    else:
        if response.status == STATUS_QUERY_SUCCESS:
            LOGGER.debug('succeeded get response from kuaidi100: %(url)s, %(response)s', {'url': url, 'response': response})
            return response
        elif response.status == STATUS_QUERY_ERROR:
            LOGGER.error('kaudi100 error: %(url)s, %(response)s', {'url': url, 'response': response})
        elif response.status == STATUS_NO_INFO_YET:
            if all(keyword in response.message for keyword in ('IP地址', '禁止')):
                raise IPBlockedException('IP blocked by kuaidi100: {}'.format(response))
            else:
                LOGGER.info('kaudi100 has no info yet: %(url)s, %(response)s', {'url': url, 'response': response})
    return {}


class IPBlockedException(Exception):
    pass
