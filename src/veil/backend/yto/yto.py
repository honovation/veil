# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import base64
import re
from hashlib import md5
from dateutil.parser import parse
import lxml
from veil.model.collection import *
from veil.utility.http import *
from veil.utility.encoding import *
from veil.utility.clock import *
from .yto_client_installer import yto_client_config

LOGGER = logging.getLogger(__name__)

STATUS_SENT_SCAN = 'SENT_SCAN'
STATUS_SIGNED = 'SIGNED'
STATUS_REJECTED = 'REJECTED'
STATUS_FAILED = 'FAILED'
REJECTED_REMARK = '收方客户拒收'
STATUS2LABEL = {
    'GOT': '揽收成功',
    'NOT_SEND': '揽收失败',
    STATUS_SENT_SCAN: '派件扫描',
    STATUS_SIGNED: '签收成功',
    STATUS_REJECTED: '签收失败'
}


def verify_logistics_notify(notify_data, sign):
    config = yto_client_config()
    return sign == base64.b64encode(md5(to_str('{}{}'.format(notify_data, config.partner_id))).digest())


def parse_logistics_notify(notify_data):
    root = lxml.objectify.fromstring(notify_data)
    accepted_at = convert_datetime_to_client_timezone(parse(root.acceptTime.text))
    notification = DictObject(logistics_id=root.txLogisticID.text, client_id=root.clientID.text, accepted_at=accepted_at,
        info_type=root.infoType.text, info_content=root.infoContent.text, status=root.infoContent.text, brief=STATUS2LABEL.get(root.infoContent.text),
        is_delivered=False, is_signed=False, is_rejected=False)
    if notification.info_type == 'STATUS':
        element_remark = root.find('remark')
        notification.remark = element_remark.text if element_remark else None
        element_name = root.find('name')
        notification.name = element_name.text if element_name else None
        if notification.status == STATUS_SENT_SCAN:
            notification.brief = '：'.join(e for e in [STATUS2LABEL[STATUS_SENT_SCAN], notification.remark] if e)
        elif notification.status in (STATUS_FAILED, STATUS_SIGNED):
            notification.is_signed, notification.is_rejected = get_delivery_status(notification)
            notification.is_delivered = notification.is_signed or notification.is_rejected
            if notification.is_signed:
                notification.brief = '{} 签收人：{}'.format(STATUS2LABEL[STATUS_SIGNED], notification.name or '-')
                if notification.remark:
                    notification.brief = '{} ({})'.format(notification.brief, notification.remark)
            elif notification.is_rejected:
                notification.brief = '{} 原因：{}'.format(STATUS2LABEL[STATUS_REJECTED], notification.remark or '-')
    return notification


def get_delivery_status(notification):
    if notification.status == STATUS_FAILED:
        return False, notification.remark == REJECTED_REMARK
    if notification.status == STATUS_SIGNED:
        if notification.name and '退' in notification.name:
            if notification.name.startswith('退'):
                return False, True
            else:
                LOGGER.warn('maybe new pattern of deliovery rejection: %(logistics_id)s, %(name)s', {
                    'logistics_id': notification.logistics_id, 'name': notification.name
                })
        return True, False
    return False, False


def subscribe_logistics_notify(logistics_id, logistics_order):
    config = yto_client_config()
    sign = base64.b64encode(md5(to_str('{}{}'.format(logistics_order, config.partner_id))).digest())
    data = {
        'logistics_interface': to_str(logistics_order),
        'data_digest': sign,
        'type': config.type,
        'clientId': config.client_id
    }
    response = to_unicode(http_call('Subscribe-purchases-logistics-status', config.api_url, data=data,
        content_type='application/x-www-form-urlencoded; charset=UTF-8'))
    if '<success>false</success>' in response:
        reason = re.findall('<reason>(.*)</reason>', response)[0]
        LOGGER.info('Failed to subscribe logistics notify: %(logistics_id)s, %(reason)s', {'logistics_id': logistics_id, 'reason': reason})
        raise Exception('Failed to subscribe logistics notify: {}, {}'.format(logistics_id, reason))
    elif '<success>true</success>' in response:
        LOGGER.info('Subscribed logistics notify successfully: %(logistics_id)s', {'logistics_id': logistics_id})
        return True
    else:
        LOGGER.info('Got error response to logistics-notify subscription from yto: %(response)s', {'response': response})
    return False
