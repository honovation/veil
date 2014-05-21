from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

add_application_sub_resource('sendgrid_client', lambda config: sendgrid_client_resource(**config))

@composite_installer
def sendgrid_client_resource(username, password):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'sendgrid-client.cfg',
        content=render_config('sendgrid-client.cfg.j2', username=username, password=password)))
    return resources


def load_sendgrid_client_config():
    return load_config_from(VEIL_ETC_DIR / 'sendgrid-client.cfg', 'username', 'password')


_config = None
def sendgrid_client_config():
    global _config
    if _config is None:
        _config = load_sendgrid_client_config()
    return _config
