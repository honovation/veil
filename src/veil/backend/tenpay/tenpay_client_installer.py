from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

_config = None

add_application_sub_resource('tenpay_client', lambda config: tenpay_client_resource(**config))


@composite_installer
def tenpay_client_resource(partner_id, app_key):
    return [file_resource(path=VEIL_ETC_DIR / 'tenpay-client.cfg', content=render_config('tenpay-client.cfg.j2', partner_id=partner_id, app_key=app_key))]


def load_tenpay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'tenpay-client.cfg', 'partner_id', 'app_key')


def tenpay_client_config():
    global _config
    if _config is None:
        _config = load_tenpay_client_config()
    return _config
