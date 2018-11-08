from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = None


@composite_installer
def queue_client_resource(host, port):
    return [file_resource(path=VEIL_ETC_DIR / 'queue-client.cfg', content=render_config('queue-client.cfg.j2', host=host, port=port))]


def load_queue_client_config():
    config = load_config_from(VEIL_ETC_DIR / 'queue-client.cfg', 'host', 'port')
    config.port = int(config.port)
    return config


def queue_client_config():
    global _config
    if _config is None:
        _config = load_queue_client_config()
    return _config
