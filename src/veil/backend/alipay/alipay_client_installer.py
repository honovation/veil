from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

_config = None

add_application_sub_resource('alipay_client', lambda config: alipay_client_resource(**config))


@composite_installer
def alipay_client_resource(partner_id, app_key, seller_email, alipay_public_key, rsa_public_key, rsa_private_key):
    resources = [
        file_resource(path=VEIL_ETC_DIR / 'alipay-client.cfg',
                      content=render_config('alipay-client.cfg.j2', partner_id=partner_id, app_key=app_key, seller_email=seller_email,
                                            alipay_public_key=alipay_public_key, rsa_public_key=rsa_public_key, rsa_private_key=rsa_private_key))
    ]
    if VEIL_ENV_TYPE in {'development', 'test'}:
        resources.extend([
            symbolic_link_resource(path='/etc/ssl/certs/alipay.pub.pem', to=VEIL_HOME / 'alipay.pub.pem'),
            symbolic_link_resource(path='/etc/ssl/certs/alipay_app.pub.pem', to=VEIL_HOME / 'alipay_app.pub.pem'),
            symbolic_link_resource(path='/etc/ssh/alipay_app.pri.pem', to=VEIL_HOME / 'alipay_app.pri.pem')
        ])
    return resources


def load_alipay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'alipay-client.cfg', 'partner_id', 'app_key', 'seller_email', 'rsa_public_key', 'rsa_private_key')


def alipay_client_config():
    global _config
    if _config is None:
        _config = load_alipay_client_config()
    return _config
