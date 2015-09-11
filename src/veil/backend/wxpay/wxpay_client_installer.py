from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

add_application_sub_resource('wxpay_client', lambda config: wxpay_client_resource(**config))
add_application_sub_resource('wx_open_app', lambda config: wx_open_app_resource(**config))


@composite_installer
def wxpay_client_resource(app_id, app_secret, partner_id, partner_key, pay_sign_key):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'wxpay-client.cfg',
        content=render_config('wxpay-client.cfg.j2', app_id=app_id, app_secret=app_secret, partner_id=partner_id, partner_key=partner_key, pay_sign_key=pay_sign_key)))
    return resources


def load_wxpay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'wxpay-client.cfg', 'app_id', 'partner_id', 'partner_key', 'pay_sign_key')


_wxpay_config = None


def wxpay_client_config():
    global _wxpay_config
    if _wxpay_config is None:
        _wxpay_config = load_wxpay_client_config()
    return _wxpay_config


@composite_installer
def wx_open_app_resource(app_id, app_secret, mch_id, api_key):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(path=VEIL_ETC_DIR / 'wx_open_app.cfg', content=render_config('wx_open_app.cfg.j2', app_id=app_id, app_secret=app_secret, mch_id=mch_id, api_key=api_key))
    )
    return resources


def load_wx_open_app_config():
    return load_config_from(VEIL_ETC_DIR / 'wx_open_app.cfg', 'app_id', 'api_key', 'mch_id')


_wx_open_app_config = None


def wx_open_app_config():
    global _wx_open_app_config
    if _wx_open_app_config is None:
        _wx_open_app_config = load_wx_open_app_config()
    return _wx_open_app_config
