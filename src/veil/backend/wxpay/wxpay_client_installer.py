from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

add_application_sub_resource('wxpay_client', lambda config: wxpay_client_resource(**config))


@composite_installer
def wxpay_client_resource(app_id, app_secret, partner_id, partner_key, pay_sign_key):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'wxpay-client.cfg',
        content=render_config('wxpay-client.cfg.j2', app_id=app_id, app_secret=app_secret, partner_id=partner_id, partner_key=partner_key, pay_sign_key=pay_sign_key)))
    return resources


def load_wxpay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'wxpay-client.cfg', 'app_id', 'partner_id', 'partner_key', 'pay_sign_key')


_config = None
def wxpay_client_config():
    global _config
    if _config is None:
        _config = load_wxpay_client_config()
    return _config
