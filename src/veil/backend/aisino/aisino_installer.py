# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os

from veil.environment import *
from veil.server.config import *
from veil.server.os import *
from veil.utility.setting import *
from veil.utility.shell import *
from veil_installer import *

from .aisino import REQUEST_AND_RESPONSE_LOG_DIRECTORY_BASE, AISINO_SHARED_LIBRARY_NAME

AISINO_SHARED_LIBRARY_CONF_PATH = '/etc/ld.so.conf.d/aisino.conf'
AISINO_SHARED_LIBRARY_PATH = DEPENDENCY_DIR / 'aisino'

RESOURCE_KEY = 'veil.backend.aisino.aisino_invoice_resource'
RESOURCE_VERSION = '1'


_config = None

add_application_sub_resource('aisino_invoice', lambda config: aisino_invoice_resource(**config))


@composite_installer
def aisino_invoice_resource(payer_id, payer_name, payer_auth_code, payer_address, payer_telephone, payer_bank_name, payer_bank_account_no, ebp_code,
                            registration_no, operator_name):
    install_aisino_shared_library()
    resources = list(BASIC_LAYOUT_RESOURCES)
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


def install_aisino_shared_library():
    url = '{}/libSOFJni_x64.so.1'.format(DEPENDENCY_URL)
    dest_path = DEPENDENCY_DIR / 'aisino'
    if not dest_path.exists():
        dest_path.mkdir()
    destination = dest_path / AISINO_SHARED_LIBRARY_NAME
    if not os.path.exists(destination):
        shell_execute('wget -c {} -O {}'.format(url, destination))
    if is_shared_library_installed():
        if VEIL_ENV_TYPE in {'development', 'test'} and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    install_resource(file_resource(path=AISINO_SHARED_LIBRARY_CONF_PATH, content=AISINO_SHARED_LIBRARY_PATH))
    shell_execute('ldconfig')
    if VEIL_ENV_TYPE in {'development', 'test'}:
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)


def is_shared_library_installed():
    if not os.path.exists(AISINO_SHARED_LIBRARY_CONF_PATH):
        return False
    with open(AISINO_SHARED_LIBRARY_CONF_PATH, 'rb') as f:
        return AISINO_SHARED_LIBRARY_PATH == f.read()
