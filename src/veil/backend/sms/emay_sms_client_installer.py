from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

add_application_sub_resource('emay_sms_client', lambda config: emay_sms_client_resource(**config))

@composite_installer
def emay_sms_client_resource(cdkey, password):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'emay-sms-client.cfg',
        content=render_config('emay-sms-client.cfg.j2', cdkey=cdkey, password=password)))
    return resources


def load_emay_sms_client_config():
    return load_config_from(VEIL_ETC_DIR / 'emay-sms-client.cfg', 'cdkey', 'password')


config = None
def emay_sms_client_config():
    global config
    if config is None:
        config = load_emay_sms_client_config()
    return config
