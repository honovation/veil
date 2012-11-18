from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def redis_program(purpose, host, port):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}_redis.conf'.format(purpose)),
            'installer_providers': ['veil.backend.redis'],
            'redis_resource': {
                'purpose': purpose,
                'host': host,
                'port': port
            }
        }
    })