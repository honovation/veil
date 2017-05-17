# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import base64
import re
from hashlib import md5
from uuid import uuid4

import lxml.objectify

from veil.backend.queue import *
from veil.frontend.cli import *
from veil.model.event import *
from veil.frontend.template import *
from veil.model.collection import *
from veil.utility.http import *
from veil.utility.encoding import *
from veil.utility.clock import *
from veil.utility.shell import *
from .yto_client_installer import yto_client_config, YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE

LOGGER = logging.getLogger(__name__)

EVENT_YTO_LOGISTICS_NOTIFICATION_RECEIVED = define_event('yto-logistics-notification-received')


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

PATTERN_FOR_REASON = re.compile('<reason>(.*?)</reason>')


def sign_md5(data):
    config = yto_client_config(purpose='public')
    return base64.b64encode(md5(to_str('{}{}'.format(data, config.partner_id))).digest())


def parse_logistics_notify(notify_data):
    root = lxml.objectify.fromstring(notify_data)
    accepted_at = convert_datetime_to_client_timezone(parse(root.acceptTime.text))
    notification = DictObject(logistics_id=root.txLogisticID.text, client_id=root.clientID.text, accepted_at=accepted_at, info_type=root.infoType.text,
                              info_content=root.infoContent.text, status=root.infoContent.text, brief=STATUS2LABEL.get(root.infoContent.text),
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
    """
    subscribe logistics notification from yto
    @param logistics_id: customized logistics id
    @param logistics_order: xml format data, see yto documents
    @return: None if succeed, exception if failed
    """
    config = yto_client_config(purpose='public')
    with require_current_template_directory_relative_to():
        logistics_order = get_template('request_order.xml').render(config=config, logistics_order=logistics_order, logistics_id=logistics_id)
    sign = sign_md5(logistics_order)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    data = {'logistics_interface': to_str(logistics_order), 'data_digest': sign, 'type': config.type, 'clientId': config.client_id}
    try:
        response = requests.post(config.api_url, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('yto logistics subscribe exception-thrown: %(data)s, %(headers)s', {'data': data, 'headers': headers})
        raise
    else:
        if '<success>true</success>' in response.text:
            LOGGER.info('yto logistics subscribe succeeded: %(logistics_id)s', {'logistics_id': logistics_id})
        elif '<success>false</success>' in response.text:
            m = PATTERN_FOR_REASON.search(response.text)
            reason = m.group(1) if m else ''
            LOGGER.info('yto logistics subscribe failed: %(logistics_id)s, %(logistics_order)s, %(reason)s', {
                'logistics_id': logistics_id,
                'reason': reason,
                'logistics_order': logistics_order
            })
            raise Exception('yto logistics subscribe failed: {}, {}'.format(logistics_id, reason))
        else:
            LOGGER.info('yto logistics subscribe failed with bad response: %(logistics_id)s, %(logistics_order)s, %(response)s', {
                'logistics_id': logistics_id,
                'response': response.text,
                'logistics_order': logistics_order
            })
            raise Exception('yto logistics subscribe failed with bad response: {}, {}'.format(logistics_id, response.text))


def query_logistics_status(trace_code):
    config = yto_client_config(purpose='public')
    with require_current_template_directory_relative_to():
        query_order = get_template('query_order.xml').render(client_id=config.client_id, trace_code=trace_code)
    sign = sign_md5(query_order)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    data = {'logistics_interface': to_str(query_order), 'data_digest': sign, 'type': config.type, 'clientId': config.client_id}
    try:
        response = requests.post(config.api_url, data=data, headers=headers, timeout=(3.05, 9), max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('yto logistics query exception-thrown: %(data)s, %(headers)s', {'data': data, 'headers': headers})
        raise
    else:
        LOGGER.debug(response.text)
        query_result = lxml.objectify.fromstring(response.text)
        logistics_status = DictObject(traces=[], signed=False, rejected=False)
        for step in query_result.orders.order.steps.iterchildren():
            step_created_at = convert_datetime_to_client_timezone(parse(step.acceptTime.text))
            if step.name.text and '退' in step.name.text:
                logistics_status.rejected = True
            logistics_status.traces.append(DictObject(brief='{} {} {}'.format(step.remark.text or '', step.acceptAddress.text or '', step.name.text or ''),
                                                      created_at=step_created_at))
        if query_result.orders.order.orderStatus.text == STATUS_SIGNED and not logistics_status.rejected:
            logistics_status.signed = True
        logistics_status.latest_biz_time = logistics_status.traces[-1].created_at
        return logistics_status


def process_logistics_notification(arguments):
    raw_notification = arguments.logistics_interface
    notification = parse_logistics_notify(raw_notification)

    record_yto_notification(notification.logistics_id, arguments)

    config = yto_client_config(purpose='public')
    if notification.client_id != config.client_id:
        return '''
            <Response>
                <logisticProviderID>YTO</logisticProviderID>
                <txLogisticID>{}</txLogisticID>
                <success>false</success>
            </Response>
            '''.format(notification.logistics_id)
    if arguments.data_digest != sign_md5(raw_notification):
        return '''
            <Response>
                <logisticProviderID>YTO</logisticProviderID>
                <txLogisticID>{}</txLogisticID>
                <success>false</success>
            </Response>
            '''.format(notification.logistics_id)
    if notification.is_delivered:
        publish_event(EVENT_YTO_LOGISTICS_NOTIFICATION_RECEIVED, notification=notification)
    return '''
            <Response>
                <logisticProviderID>YTO</logisticProviderID>
                <txLogisticID>{}</txLogisticID>
                <success>true</success>
            </Response>
            '''.format(notification.logistics_id)


def record_yto_notification(logistics_id, raw_notification):
    LOGGER.info('[YTO-IN]received request payload: %(logistics_id)s, %(payload)s', {
        'logistics_id': logistics_id,
        'payload': raw_notification
    })
    current_time_string = get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S')
    log_file_name = '{}-{}-{}.xml'.format(logistics_id, current_time_string, uuid4().hex)
    log_file_dir = YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE / current_time_string[:4] / current_time_string[4:6] / current_time_string[6:8]
    log_file_dir.makedirs()
    with open(log_file_dir / log_file_name, mode='wb+') as f:
        f.write(to_str(raw_notification))


@script('query-status')
def query_logistics_status_script(trace_code):
    print(query_logistics_status(trace_code))


@periodic_job('23 0 * * *')
def clean_up_yto_incoming_request_files_job():
    if not YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE.exists():
        return
    shell_execute('find {} -type f -mtime +30 -delete'.format(YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE), capture=True)
    try:
        shell_execute('find {} -type d -mtime +30 -delete'.format(YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE), capture=True)
    except ShellExecutionError as err:
        LOGGER.error('delete dir got error: %(output)s', {'output': err.output})
