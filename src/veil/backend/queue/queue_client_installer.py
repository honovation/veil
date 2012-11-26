from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('queue_client')
def install_queue_client(type, host, port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(VEIL_ETC_DIR / 'queue-client.cfg', content=render_config(
            'queue-client.cfg.j2', type=type, host=host, port=port)))
    return [], resources


def load_queue_client_config():
    config = load_config_from(VEIL_ETC_DIR / 'queue-client.cfg',
        'type', 'host', 'port')
    config.port = int(config.port)
    return config