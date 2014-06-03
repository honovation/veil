# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import base64
import re
from hashlib import md5
from veil.utility.http import *
from veil.utility.encoding import *
from .yto_client_installer import yto_client_config

LOGGER = logging.getLogger(__name__)

YTO_SIGNED_STATUS = 'SIGNED'
YTO_REJECTED_STATUS = 'FAILED'
YTO_STATUS = {
    'GOT': '揽收成功',
    'NOT_SEND': '揽收失败',
    'SENT_SCAN': '派件扫描',
    YTO_SIGNED_STATUS: '签收成功',
    YTO_REJECTED_STATUS: '签收失败'
}


def verify_request(data, sign):
    config = yto_client_config()
    return sign == base64.b64encode(md5(to_str('{}{}'.format(data, config.partner_id))).digest())


def get_brief(status_obj):
    if status_obj.infoContent.text == 'SENT_SCAN':
        return '{}：{}'.format(YTO_STATUS['SENT_SCAN'], status_obj.remark.text)
    elif status_obj.infoContent.text == YTO_REJECTED_STATUS:
        return '{} 原因：{}'.format(YTO_STATUS[YTO_REJECTED_STATUS], status_obj.remark.text)
    elif status_obj.infoContent.text == YTO_SIGNED_STATUS:
        result = '{} 签收人：{}'.format(YTO_STATUS[YTO_SIGNED_STATUS], status_obj.name.text)
        if status_obj.remark.text:
            return '{} ({})'.format(result, status_obj.remark.text)
        return result
    else:
        return YTO_STATUS.get(status_obj.infoContent.text)


def subscribe(purchase_id, purchase_xml_data):
    config = yto_client_config()
    purchase_data_digest = base64.b64encode(md5(to_str('{}{}'.format(purchase_xml_data, config.partner_id))).digest())
    data = {
        'logistics_interface': to_str(purchase_xml_data),
        'data_digest': purchase_data_digest,
        'type': config.type,
        'clientId': config.client_id
    }
    response = to_unicode(http_call('Subscribe-purchases-logistics-status', config.api_url, data=data,
        content_type='application/x-www-form-urlencoded; charset=UTF-8'))
    if '<success>false</success>' in response:
        reason = re.findall('<reason>(.*)</reason>', response)[0]
        LOGGER.info('Failed subscribe purchases logistics status: %(purchase_id)s, %(reason)s', {'purchase_id': purchase_id, 'reason': reason})
        raise SubscribeLogisticsStatusException('Failed subscribe purchases logistics status: {} {}'.format(purchase_id, reason))
    elif '<success>true</success>' in response:
        LOGGER.info('Subscribe purchases logistics status successfully: %(purchase_id)s', {'purchase_id': purchase_id})
        return True
    else:
        LOGGER.info('Get error response from yto: %(response)s', {'response': response})
    return False


class SubscribeLogisticsStatusException(Exception):
    pass