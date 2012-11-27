from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def redis_program(purpose, host, port):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-'))),
            'resources': [('veil.backend.redis.redis_server_resource', {
                'purpose': purpose,
                'host': host,
                'port': port
            })]
        }
    })


def redis_client_resource(purpose, host, port):
    return ('veil.backend.redis.redis_client_resource', {
        'purpose': purpose,
        'host': host,
        'port': port
    })


