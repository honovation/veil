# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os

from veil.environment import *
from veil.server.config import *
from veil.server.os import *
from veil.utility.setting import *
from veil.utility.shell import *
from veil_installer import *

from .aisino import REQUEST_AND_RESPONSE_LOG_DIRECTORY_BASE, AISINO_JAR_FILE_NAME, AISINO_JAR_PATH, AISINO_JAR_FILE_PATH

RESOURCE_KEY = 'veil.backend.aisino.aisino_invoice_resource'
RESOURCE_VERSION = '1.0'


_config = None

add_application_sub_resource('aisino_invoice', lambda config: aisino_invoice_resource(**config))


@composite_installer
def aisino_invoice_resource(payer_id, payer_name, payer_auth_code, payer_address, payer_telephone, payer_bank_name, payer_bank_account_no, ebp_code,
                            registration_no, operator_name):
    resources = list(BASIC_LAYOUT_RESOURCES)
    install_aisino_jar()
    resources.append(directory_resource(path=REQUEST_AND_RESPONSE_LOG_DIRECTORY_BASE, owner=CURRENT_USER, group=CURRENT_USER_GROUP))
    resources.append(file_resource(path=VEIL_ETC_DIR / 'aision_invoice.cfg', content=render_config('aision_invoice.cfg.j2',
                                                                                                   payer_id=payer_id,
                                                                                                   payer_name=payer_name,
                                                                                                   payer_auth_code=payer_auth_code,
                                                                                                   payer_address=payer_address,
                                                                                                   payer_telephone=payer_telephone,
                                                                                                   payer_bank_name=payer_bank_name,
                                                                                                   payer_bank_account_no=payer_bank_account_no,
                                                                                                   ebp_code=ebp_code,
                                                                                                   registration_no=registration_no,
                                                                                                   operator_name=operator_name)))
    return resources


def load_aisino_invoice_config():
    return load_config_from(VEIL_ETC_DIR / 'aision_invoice.cfg', 'payer_id', 'payer_name', 'payer_auth_code', 'payer_address', 'payer_telephone',
                            'payer_bank_name', 'payer_bank_account_no', 'ebp_code', 'registration_no', 'operator_name')


def aisino_invoice_config():
    global _config
    if _config is None:
        _config = load_aisino_invoice_config()
    return _config


def install_aisino_jar():
    url = '{}/{}'.format(DEPENDENCY_URL, AISINO_JAR_FILE_NAME)
    dest_path = AISINO_JAR_PATH
    if not dest_path.exists():
        dest_path.mkdir()
    if not os.path.exists(AISINO_JAR_FILE_PATH):
        shell_execute('wget -c {} -O {}'.format(url, AISINO_JAR_FILE_PATH))
    if VEIL_ENV_TYPE in {'development', 'test'}:
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
