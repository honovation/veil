# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import *
from veil.server.config import *
from veil.server.os import *
from veil.utility.setting import *
from veil.utility.shell import *
from veil_installer import *


AISINO_JNI_FILE_NAME = 'libSOFJni_x64.so'
AISINO_LIBRARY_CONFIG_FILE_NAME = 'pkcs7.properties'
AISINO_JAR_FILE_NAME = 'aisino-1.2.jar'
AISINO_LIBRARY_PATH = DEPENDENCY_DIR / 'aisino'
AISINO_JAR_FILE_PATH = AISINO_LIBRARY_PATH / AISINO_JAR_FILE_NAME
AISINO_LIBRARY_CONFIG_FILE_PATH = AISINO_LIBRARY_PATH / AISINO_LIBRARY_CONFIG_FILE_NAME
AISINO_JNI_FILE_PATH = AISINO_LIBRARY_PATH / AISINO_JNI_FILE_NAME
AISINO_PLATFORM_CER_FILE_NAME = '51fapiao.cer'
AISINO_PLATFORM_CER_FILE_PATH = AISINO_LIBRARY_PATH / AISINO_PLATFORM_CER_FILE_NAME
RESOURCE_KEY = 'veil.backend.aisino.aisino_invoice_resource'
REQUEST_AND_RESPONSE_LOG_DIRECTORY_BASE = VEIL_BUCKET_LOG_DIR / 'aisino'
RESOURCE_VERSION = '1.0'


_config = None

add_application_sub_resource('aisino_invoice', lambda config: aisino_invoice_resource(**config))


@composite_installer
def aisino_invoice_resource(seq_prefix, payer_id, payer_name, payer_auth_code, payer_address, payer_telephone, payer_bank_name, payer_bank_account_no, ebp_code,
                            registration_no, operator_name, receiver_operator_name, recheck_operator_name, client_pfx, client_pfx_key):
    install_aisino_library()
    config_file_content = render_config('pkcs7.properties.j2', client_pfx=client_pfx, client_pfx_key=client_pfx_key,
                                        platform_cer=AISINO_PLATFORM_CER_FILE_PATH, jni_library=AISINO_JNI_FILE_PATH)
    if AISINO_LIBRARY_CONFIG_FILE_PATH.exists() and AISINO_LIBRARY_CONFIG_FILE_PATH.bytes() == config_file_content:
        resources = []
    else:
        resources = [file_resource(path=AISINO_LIBRARY_CONFIG_FILE_PATH, content=config_file_content)]
    resources.extend([
        directory_resource(path=REQUEST_AND_RESPONSE_LOG_DIRECTORY_BASE, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'aision_invoice.cfg',
                      content=render_config('aision_invoice.cfg.j2', seq_prefix=seq_prefix, payer_id=payer_id, payer_name=payer_name,
                                            payer_auth_code=payer_auth_code, payer_address=payer_address, payer_telephone=payer_telephone,
                                            payer_bank_name=payer_bank_name, payer_bank_account_no=payer_bank_account_no, ebp_code=ebp_code,
                                            registration_no=registration_no, operator_name=operator_name, receiver_operator_name=receiver_operator_name,
                                            recheck_operator_name=recheck_operator_name))
    ])
    return resources


def load_aisino_invoice_config():
    return load_config_from(VEIL_ETC_DIR / 'aision_invoice.cfg', 'seq_prefix', 'payer_id', 'payer_name', 'payer_auth_code', 'payer_address', 'payer_telephone',
                            'payer_bank_name', 'payer_bank_account_no', 'ebp_code', 'registration_no', 'operator_name', 'receiver_operator_name',
                            'recheck_operator_name')


def aisino_invoice_config():
    global _config
    if _config is None:
        _config = load_aisino_invoice_config()
    return _config


def install_aisino_library():
    if AISINO_JAR_FILE_PATH.exists() and AISINO_JNI_FILE_PATH.exists() and AISINO_PLATFORM_CER_FILE_PATH.exists():
        if (VEIL_ENV.is_dev or VEIL_ENV.is_test) and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    dest_path = AISINO_LIBRARY_PATH
    if not dest_path.exists():
        dest_path.mkdir()
    install_aisino_platform_cer()
    install_aisino_jni_library()
    install_aisino_jar()
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)


def install_aisino_jni_library():
    url = '{}/{}'.format(DEPENDENCY_SSL_URL, AISINO_JNI_FILE_NAME)
    if not AISINO_JNI_FILE_PATH.exists():
        shell_execute('wget --no-check-certificate -c {} -O {}'.format(url, AISINO_JNI_FILE_PATH))


def install_aisino_jar():
    url = '{}/{}'.format(DEPENDENCY_SSL_URL, AISINO_JAR_FILE_NAME)
    if not AISINO_JAR_FILE_PATH.exists():
        shell_execute('wget --no-check-certificate -c {} -O {}'.format(url, AISINO_JAR_FILE_PATH))


def install_aisino_platform_cer():
    url = '{}/{}'.format(DEPENDENCY_SSL_URL, AISINO_PLATFORM_CER_FILE_NAME)
    if not AISINO_PLATFORM_CER_FILE_PATH.exists():
        shell_execute('wget --no-check-certificate -c {} -O {}'.format(url, AISINO_PLATFORM_CER_FILE_PATH))
