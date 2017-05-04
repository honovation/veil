from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = None


@composite_installer
def kuaidi100_client_resource(api_id):
    return [file_resource(path=VEIL_ETC_DIR / 'kuaidi100-client.cfg', content=render_config('kuaidi100-client.cfg.j2', api_id=api_id))]


def load_kuaidi100_client_config():
    return load_config_from(VEIL_ETC_DIR / 'kuaidi100-client.cfg', 'api_id')


def kuaidi100_client_config():
    global _config
    if _config is None:
        _config = load_kuaidi100_client_config()
    return _config
