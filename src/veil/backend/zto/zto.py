# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import json
import base64
import re
from hashlib import md5
from uuid import uuid4

from veil.backend.job_queue import *
from veil.model.event import *
from veil.model.binding import *
from veil.utility.clock import *
from veil.frontend.cli import *
from veil.model.collection import *
from veil.utility.http import *
from veil.utility.encoding import *
from veil.utility.json import *
from veil.utility.shell import *
from veil_component import VEIL_ENV
from .zto_client_installer import zto_client_config, ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE

LOGGER = logging.getLogger(__name__)

EVENT_ZTO_LOGISTICS_NOTIFICATION_RECEIVED = define_event('zto-logistics-notification-received')

API_URL = 'http://japi.zto.cn/gateway.do'
if VEIL_ENV.is_prod:
    SUBSCRIBE_LOGISTICS_NOTIFICATION_URL = 'http://japi.zto.cn/zto/api_utf8/subBillLog'
else:
    SUBSCRIBE_LOGISTICS_NOTIFICATION_URL = 'http://58.40.16.125:9001/zto/api_utf8/subBillLog'
QUERY_LOGISTICS_STATUS_MSG_CODE = 'TRACEINTERFACE_NEW_TRACES'
SIGN_SCAN_TYPE = '签收'
TRD_SIGN_SCAN_TYPE = '第三方签收'
REJECT_SCAN_TYPE = '退件签收'
NOTIFICATION_SIGN_SCAN_TYPE = 'SIGN'
NOTIFICATION_REJECT_SCAN_TYPE = 'RESIGN'
SUBSCRIBE_MSG_TYPE = 'SUB'
UNSUBSCRIBE_MSG_TYPE = 'CANCEL'
SUBSCRIBE_ALL_EVENTS = 63


def query_logistics_status(*bill_codes):
    config = zto_client_config()
    data = DictObject(company_id=config.company_id, msg_type=QUERY_LOGISTICS_STATUS_MSG_CODE, data=json.dumps(list(bill_codes)))
    data.data_digest = sign_md5(data.data)
    response = None
    try:
        response = requests.post(API_URL, data=data, headers={'ContentType': 'application/x-www-form-urlencoded; charset=UTF-8'}, timeout=(3.05, 15),
                                 max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('Got exception when query zto logistics status: %(bill_codes)s, %(response)s, %(status_code)s', {
            'bill_codes': bill_codes,
            'response': response.text if response else '',
            'status_code': response.status_code if response else ''
        })
        raise
    else:
        LOGGER.debug('query logistics status success: %(response)s', {
            'response': response.text
        })
        try:
            json_response = objectify(response.json())
        except Exception as e:
            LOGGER.exception('Got exception when parse zto logistics status response: %(response)s, %(message)s, %(data)s', {
                'response': response.text,
                'message': e.message,
                'data': data
            })
            raise
        else:
            if not json_response.status:
                LOGGER.error('Got failed response when query zto logistics status: %(message)s, %(response)s, %(data)s', {
                    'response': response.text,
                    'message': json_response.message,
                    'data': data
                })
            else:
                if json_response.data is None:
                    json_response.data = []
                bill_code2logistics_status = {
                    d.billCode: DictObject(traces=[DictObject(brief=t.desc, status_code=t.scanType, created_at=t.scanDate) for t in d.traces],
                                           signed=d.traces[-1].scanType in (SIGN_SCAN_TYPE, TRD_SIGN_SCAN_TYPE),
                                           rejected=d.traces[-1].scanType == REJECT_SCAN_TYPE,
                                           latest_biz_time=convert_datetime_to_client_timezone(to_datetime()(d.traces[-1].scanDate)))
                    for d in json_response.data
                }
                LOGGER.debug(bill_code2logistics_status)
                return bill_code2logistics_status


def sign_md5(data, api_key=None):
    api_key = api_key or zto_client_config().api_key
    return base64.b64encode(md5(to_str('{}{}'.format(data, api_key))).digest())


def subscribe_logistics_notify(logistics_id, logistics_order, msg_type=SUBSCRIBE_MSG_TYPE):
    """
    subscribe logistics notification from zto

    @param logistics_id: customized logistics id
    @param logistics_order: DictObject(trace_code=, notify_url=)
    @param msg_type: default subscribe notification
    @return: None if succeed, exception if failed
    """
    config = zto_client_config()
    company_id = config.company_id if VEIL_ENV.is_prod else 'test'
    create_by = config.subscribe_create_by if VEIL_ENV.is_prod else 'test'
    data_ = [DictObject(id=logistics_id, billCode=logistics_order.trace_code, pushCategory='callBack', pushTarget=logistics_order.notify_url,
                        subscriptionCategory=SUBSCRIBE_ALL_EVENTS, createBy=create_by)]
    data = DictObject(msg_type=msg_type, company_id=company_id, data=json.dumps(data_))
    data.data_digest = sign_md5(data.data)
    response = None
    try:
        response = requests.post(SUBSCRIBE_LOGISTICS_NOTIFICATION_URL, data=data, headers={'ContentType': 'application/x-www-form-urlencoded; charset=UTF-8'},
                                 timeout=(3.05, 15), max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception as e:
        LOGGER.exception('Got exception when subscribe logistics notification from zto: %(data)s, %(message)s, %(response)s, %(status_code)s', {
            'data': data,
            'message': e.message,
            'response': response.text if response else '',
            'status_code': response.status_code if response else ''
        })
    else:
        LOGGER.debug('call subscribe logistics notification success: %(response)s', {
            'response': response.text
        })
        if re.search(r'S\d{2}', response.text):
            LOGGER.error('Got error response when subscribe logistics notification from zto: %(response)s, %(data)s', {
                'response': response.text,
                'data': data
            })
            raise Exception('subscribe error: {}'.format(response.text))
        else:
            json_result = objectify(response.json())
            if not json_result[0].status:
                if msg_type == UNSUBSCRIBE_MSG_TYPE and '取消订阅失败' in json_result[0].remark:
                    LOGGER.info('ignore unsubscribe error if unsubscribed before: %(message)s', {
                        'message': json_result[0].remark
                    })
                    return
                LOGGER.error('Got error status when subscribe logistics notification from zto: %(response)s, %(data)s, %(message)s', {
                    'response': response.text,
                    'data': data,
                    'message': json_result[0].remark
                })
                raise Exception('subscribe error: {}'.format(json_result[0].remark))


def process_logistics_notification(arguments):
    record_zto_notification('{}-{}'.format(arguments.purchase_id, arguments.box_id), to_json(arguments))

    fail_response = DictObject(message='', result='fail', status=False, statusCode='')
    fail_message = None
    if arguments.msg_type != 'Traces':
        fail_message = 'unknown msg_type'
    else:
        config = zto_client_config()
        if arguments.company_id != config.subscribe_create_by:
            fail_message = 'company_id mismatch'
        elif sign_md5(arguments.data, api_key=config.subscribe_api_key) != arguments.data_digest:
            fail_message = 'invalid data_digest'
    if fail_message:
        LOGGER.error('Got wrong zto notification: %(message)s, %(arguments)s', {
            'message': fail_message,
            'arguments': arguments
        })
        fail_response.message = fail_message
        return fail_response

    LOGGER.info('Accepted zto notification: %(purchase_id)s, %(box_id)s', {
        'purchase_id': arguments.purchase_id,
        'box_id': arguments.box_id
    })

    arguments.data = objectify(from_json(arguments.data))
    signed_by = None
    signed = arguments.data.scanType == NOTIFICATION_SIGN_SCAN_TYPE
    if signed:
        signed_by = arguments.data.contacts
    rejected = arguments.data.scanType == NOTIFICATION_REJECT_SCAN_TYPE
    if signed or rejected:
        publish_event(EVENT_ZTO_LOGISTICS_NOTIFICATION_RECEIVED, purchase_id=arguments.purchase_id, box_id=arguments.box_id,
                      status_code=arguments.data.scanType, brief=arguments.data.desc, signed=signed, signed_by=signed_by, rejected=rejected,
                      notified_at=arguments.data.scanDate)
    return DictObject(message='', result='success', status=True, statusCode='0')


@script('subscribe')
def subscribe_notification_script(logistics_id, trace_code, notify_url, is_subscribe=True):
    msg_type = SUBSCRIBE_MSG_TYPE if to_bool(is_subscribe) else UNSUBSCRIBE_MSG_TYPE
    print(subscribe_logistics_notify(logistics_id, DictObject(trace_code=trace_code, notify_url=notify_url), msg_type=msg_type))


@script('query-status')
def query_status_script(trace_code):
    status = query_logistics_status(trace_code)[trace_code]
    print(status.signed)
    print(status.rejected)
    print(status.latest_biz_time)
    for t in status.traces:
        print('{} {} {}'.format(t.created_at, t.brief, t.status_code))


def record_zto_notification(logistics_id, raw_notification):
    LOGGER.info('[ZTO-IN]received request payload: %(logistics_id)s, %(payload)s', {
        'logistics_id': logistics_id,
        'payload': raw_notification
    })
    current_time_string = get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S')
    log_file_name = '{}-{}-{}'.format(logistics_id, current_time_string, uuid4().hex)
    log_file_dir = ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE / current_time_string[:4] / current_time_string[4:6] / current_time_string[6:8]
    log_file_dir.makedirs()
    with open(log_file_dir / log_file_name, mode='wb+') as f:
        f.write(to_str(raw_notification))


@task(queue='clean_up_zto_incoming_request_files', schedule=cron_expr('25 0 * * *'))
def clean_up_zto_incoming_request_files():
    if not ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE.exists():
        return
    shell_execute('find {} -type f -mtime +30 -delete'.format(ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE), capture=True)
    try:
        shell_execute('find {} -type d -mtime +30 -delete'.format(ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE), capture=True)
    except ShellExecutionError as err:
        LOGGER.error('delete dir got error: %(output)s', {'output': err.output})
