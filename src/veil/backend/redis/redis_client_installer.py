from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

_config = {}


@composite_installer
def redis_client_resource(purpose, host, port):
    return [
        file_resource(path=VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')),
                      content=render_config('redis-client.cfg.j2', host=host, port=port))
    ]


def load_redis_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')), 'host', 'port')
    config.port = int(config.port)
    return config


def redis_client_config(purpose):
    return _config.setdefault(purpose, load_redis_client_config(purpose))
