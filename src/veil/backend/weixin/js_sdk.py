# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from uuid import uuid4
import hashlib

from veil.profile.model import *

from .js_api_ticket import get_wxmp_jsapi_ticket


def get_js_sdk_sign(params):
    return hashlib.sha1('&'.join('{}={}'.format(k, params[k]) for k in sorted(params))).hexdigest()


def get_js_sdk_config(wxop_app_code, app_id, app_secret, url, debug, js_api_list, jsapi_config=None):
    timestamp = get_current_timestamp()
    noncestr = uuid4().get_hex()
    params = DictObject(jsapi_ticket=get_wxmp_jsapi_ticket(wxop_app_code, app_id, app_secret, jsapi_config=jsapi_config), noncestr=noncestr,
                        timestamp=timestamp, url=url)
    signature = get_js_sdk_sign(params)
    return DictObject(debug=debug, appId=jsapi_config.app_id if jsapi_config else app_id, timestamp=timestamp, nonceStr=noncestr, signature=signature,
                      jsApiList=js_api_list)
