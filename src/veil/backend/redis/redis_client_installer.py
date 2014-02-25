from __future__ import unicode_literals, print_function, division, absolute_import
from veil.profile.installer import *

@composite_installer
def redis_client_resource(purpose, host, port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(path=VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')),
            content=render_config(
                'redis-client.cfg.j2', host=host, port=port)))
    return resources


def load_redis_client_config(purpose):
    config_ = load_config_from(VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')), 'host', 'port')
    config_.port = int(config_.port)
    return config_


config = {}
def redis_client_config(purpose):
    return config.setdefault(purpose, load_redis_client_config(purpose))