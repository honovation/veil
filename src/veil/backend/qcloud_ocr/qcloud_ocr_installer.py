# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import VEIL_ETC_DIR, CURRENT_USER, CURRENT_USER_GROUP
from veil.server.config import *
from veil.server.os import *
from veil.utility.setting import *
from veil_installer import *

_config = None


@composite_installer
def qcloud_ocr_client_resource(appid, secret_id, secret_key):
    return [file_resource(path=VEIL_ETC_DIR / 'qcloud-ocr-client.cfg',
                          content=render_config('qcloud-ocr-client.cfg.j2', appid=appid, secret_id=secret_id, secret_key=secret_key),
                          owner=CURRENT_USER, group=CURRENT_USER_GROUP)]


def load_qcloud_ocr_client_config():
    return load_config_from(VEIL_ETC_DIR / 'qcloud-ocr-client.cfg', 'appid', 'secret_id', 'secret_key')


def qcloud_ocr_client_config():
    global _config
    if _config is None:
        _config = load_qcloud_ocr_client_config()
    return _config
