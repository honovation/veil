from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

add_application_sub_resource('yunpian_sms_client', lambda config: yunpian_sms_client_resource(**config))


@composite_installer
def yunpian_sms_client_resource(apikey):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'yunpian-sms-client.cfg', content=render_config('yunpian-sms-client.cfg.j2', apikey=apikey)))
    return resources


def load_yunpian_sms_client_config():
    return load_config_from(VEIL_ETC_DIR / 'yunpian-sms-client.cfg', 'apikey')


_config = None
def yunpian_sms_client_config():
    global _config
    if _config is None:
        _config = load_yunpian_sms_client_config()
    return _config
