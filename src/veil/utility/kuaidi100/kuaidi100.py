# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import socket
from time import sleep
import urllib
import urllib2
from veil.model.collection import *
from veil.utility.encoding import *
from veil.utility.json import *

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


def get_delivery_status(api_id, shipper_code, shipping_code, sleep_at_start=0, http_timeout=15):
    if 'youzhengguonei' == shipper_code: # kuaidi100 API does not support China Post yet
        return {}
    if sleep_at_start > 0:
        sleep(sleep_at_start) # avoid IP blocking due to too frequent queries
    result_json = None
    url = API_URL_TEMPLATE.format(api_id, shipper_code, urllib.quote(to_str(shipping_code)))
    exception = None
    tries = 0
    max_tries = 2
    while tries < max_tries:
        tries += 1
        if tries > 1:
            sleep(10)
        try:
            result_json = urllib2.urlopen(url, timeout=http_timeout).read()
        except Exception as e:
            exception = e
            if isinstance(e, urllib2.HTTPError):
                LOGGER.exception('kuaidi100 query service cannot fulfill the request: %(url)s', {'url': url})
                if 400 <= e.code < 500: # 4xx, client error, no retry
                    break
            elif isinstance(e, socket.timeout) or isinstance(e, urllib2.URLError) and isinstance(e.reason, socket.timeout):
                LOGGER.exception('kuaidi100 query timed out: %(timeout)s, %(url)s', {
                    'timeout': http_timeout,
                    'url': url
                })
            elif isinstance(e, urllib2.URLError):
                LOGGER.exception('cannot reach kuaidi100 query service: %(url)s', {'url': url})
            else:
                LOGGER.exception('kuaidi100 query failed: %(url)s', {'url': url})
        else:
            exception = None
            break
    if exception is None and result_json:
        result = objectify(from_json(result_json))
        if result.status == STATUS_QUERY_SUCCESS:
            LOGGER.info('succeeded get response from kuaidi100: %(result_json)s', {'result_json': result_json})
            return result
        elif result.status == STATUS_QUERY_ERROR:
            LOGGER.error('kaudi100 error: %(url)s, %(result)s', {'url': url, 'result': result})
        elif result.status == STATUS_NO_INFO_YET:
            if all(keyword in result.message for keyword in ('IP地址', '禁止')):
                raise IPBlockedException('IP blocked by kuaidi100: {}'.format(result))
            else:
                LOGGER.info('no result of this delivery number: %(result_json)', {'result_json': result_json})
    return {}


class IPBlockedException(Exception):
    pass
