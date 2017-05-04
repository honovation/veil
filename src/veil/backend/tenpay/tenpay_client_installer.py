from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

_config = None


@composite_installer
def tenpay_client_resource(partner_id, app_key, refund_op_user_id, refund_op_user_password, api_ca_cert, api_client_cert, api_client_key):
    resources = [
        file_resource(path=VEIL_ETC_DIR / 'tenpay-client.cfg', content=render_config('tenpay-client.cfg.j2', partner_id=partner_id, app_key=app_key,
                                                                                     refund_op_user_id=refund_op_user_id,
                                                                                     refund_op_user_password=refund_op_user_password,
                                                                                     api_ca_cert=api_ca_cert,
                                                                                     api_client_cert=api_client_cert, api_client_key=api_client_key))
    ]
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        resources.extend([
            symbolic_link_resource(path='/etc/ssl/certs/tenpay_ca.pem', to=VEIL_HOME / 'tenpay_ca.pem'),
            symbolic_link_resource(path='/etc/ssl/certs/tenpay_cert.pem', to=VEIL_HOME / 'tenpay_cert.pem'),
            symbolic_link_resource(path='/etc/ssh/tenpay_key.pem', to=VEIL_HOME / 'tenpay_key.pem')
        ])
    return resources


def load_tenpay_client_config():
    return load_config_from(VEIL_ETC_DIR / 'tenpay-client.cfg', 'partner_id', 'app_key', 'refund_op_user_id', 'refund_op_user_password', 'api_ca_cert',
                            'api_client_cert', 'api_client_key')


def tenpay_client_config():
    global _config
    if _config is None:
        _config = load_tenpay_client_config()
    return _config
