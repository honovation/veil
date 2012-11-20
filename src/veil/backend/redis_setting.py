from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *
from veil.environment.setting import *

def redis_program(purpose, host, port):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}_redis.conf'.format(purpose.replace('_', '-'))),
            'installer_providers': ['veil.backend.redis'],
            'resources': [('redis_server', {
                'purpose': purpose,
                'host': host,
                'port': port
            })]
        }
    })


def redis_client_resource(purpose, host, port):
    return ('redis_client', {
        'purpose': purpose,
        'host': host,
        'port': port
    })


def load_redis_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')), 'host', 'port')
    config.port = int(config.port)
    return config

