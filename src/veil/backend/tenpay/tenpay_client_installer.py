from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

add_application_sub_resource('tenpay_client', lambda config: tenpay_client_resource(**config))


@composite_installer
def tenpay_client_resource(partner_id, app_key):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'tenpay-client.cfg',
        content=render_config('tenpay-client.cfg.j2', partner_id=partner_id, app_key=app_key)))
    return resources


def load_tenpay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'tenpay-client.cfg', 'partner_id', 'app_key')


config = None
def tenpay_client_config():
    global config
    if config is None:
        config = load_tenpay_client_config()
    return config
