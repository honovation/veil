# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import json
import base64
from hashlib import md5

from veil.model.collection import *
from veil.utility.http import *
from veil.utility.encoding import *
from .zto_client_installer import zto_client_config

LOGGER = logging.getLogger(__name__)


API_URL = 'http://japi.zto.cn/gateway.do'
QUERY_LOGISTICS_STATUS_MSG_CODE = 'TRACEINTERFACE_NEW_TRACES'
SIGN_SCAN_TYPE = '签收'
TRD_SIGN_SCAN_TYPE = '第三方签收'
REJECT_SCAN_TYPE = '退件签收'


def sign_data(biz_json_data, api_key):
    return base64.b64encode(md5(to_str('{}{}'.format(biz_json_data, api_key))).digest())


def make_post_data(msg_type, biz_data):
    config = zto_client_config()
    post_data = DictObject(company_id=config.company_id, msg_type=msg_type, data=json.dumps(biz_data))
    post_data.data_digest = sign_data(post_data.data, config.api_key)
    return post_data


def query_zto_logistics_status(*bill_codes):
    data = make_post_data(QUERY_LOGISTICS_STATUS_MSG_CODE, {'billCodes': bill_codes})
    headers = {
        'ContentType': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    response = None
    try:
        response = requests.post(API_URL, data=data, headers=headers, timeout=(3.05, 15), max_retries=Retry(total=3, backoff_factor=0.5))
        response.raise_for_status()
    except Exception:
        LOGGER.exception('Got exception when query zto logistics status: %(bill_codes)s, %(response)s, %(status_code)s', {
            'bill_codes': bill_codes,
            'response': response.text if response else '',
            'status_code': response.status_code if response else ''
        })
        raise
    else:
        try:
            json_response = objectify(response.json())
        except Exception as e:
            LOGGER.exception('Got exception when parse zto logistics status response: %(response)s, %(message)s', {
                'response': response.text,
                'message': e.message
            })
            raise
        else:
            if not json_response.status:
                LOGGER.error('Got failed response when query zto logistics status: %(message)s, %(response)s', {
                    'response': response.text,
                    'message': json_response.msg
                })
            else:
                bill_code2logistics_status = {
                    d.billCode: DictObject(traces=d.traces, signed=is_signed(d.traces), rejected=is_reject(d.traces))
                    for d in json_response.data
                }
                LOGGER.debug(bill_code2logistics_status)
                return bill_code2logistics_status


def is_signed(traces):
    return traces[-1].scanType in (SIGN_SCAN_TYPE, TRD_SIGN_SCAN_TYPE)


def is_reject(traces):
    return traces[-1].scanType == REJECT_SCAN_TYPE
