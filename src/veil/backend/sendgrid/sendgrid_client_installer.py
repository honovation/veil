from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = None


@composite_installer
def sendgrid_client_resource(username, password):
    return [file_resource(path=VEIL_ETC_DIR / 'sendgrid-client.cfg', content=render_config('sendgrid-client.cfg.j2', username=username, password=password),
                          owner=CURRENT_USER, group=CURRENT_USER_GROUP)]


def load_sendgrid_client_config():
    return load_config_from(VEIL_ETC_DIR / 'sendgrid-client.cfg', 'username', 'password')


def sendgrid_client_config():
    global _config
    if _config is None:
        _config = load_sendgrid_client_config()
    return _config
