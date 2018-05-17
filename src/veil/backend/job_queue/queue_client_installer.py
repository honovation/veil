from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = None


@composite_installer
def queue_client_resource(type, host, port):
    return [file_resource(path=VEIL_ETC_DIR / 'queue-client.cfg', content=render_config('queue-client.cfg.j2', type=type, host=host, port=port),
                          owner=CURRENT_USER, group=CURRENT_USER_GROUP)]


def load_queue_client_config():
    # TODO: return a workaround config as @task is executed during import time, config file still not exist
    if (VEIL_ETC_DIR / 'queue-client.cfg').exists():
        config = load_config_from(VEIL_ETC_DIR / 'queue-client.cfg', 'type', 'host', 'port')
        config.port = int(config.port)
    else:
        config = DictObject(type='redis', host='localhost', port=6379)
    return config


def queue_client_config():
    global _config
    if _config is None:
        _config = load_queue_client_config()
    return _config
