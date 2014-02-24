from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

add_application_sub_resource('kuaidi100_client', lambda config: kuaidi100_client_resource(**config))

@composite_installer
def kuaidi100_client_resource(api_id):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / 'kuaidi100-client.cfg', content=render_config('kuaidi100-client.cfg.j2', api_id=api_id)))
    return resources


def load_kuaidi100_client_config():
    config = load_config_from(VEIL_ETC_DIR / 'kuaidi100-client.cfg', 'api_id')
    return config