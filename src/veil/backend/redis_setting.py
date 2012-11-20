from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

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


