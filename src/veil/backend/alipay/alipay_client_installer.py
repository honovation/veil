from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

add_application_sub_resource('alipay_client', lambda config: alipay_client_resource(**config))


@composite_installer
def alipay_client_resource(partner_id, app_key, seller_email):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'alipay-client.cfg',
        content=render_config('alipay-client.cfg.j2', partner_id=partner_id, app_key=app_key, seller_email=seller_email)))
    return resources


def load_alipay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'alipay-client.cfg', 'partner_id', 'app_key', 'seller_email')


_config = None
def alipay_client_config():
    global _config
    if _config is None:
        _config = load_alipay_client_config()
    return _config
