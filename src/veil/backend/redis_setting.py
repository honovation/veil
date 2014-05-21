from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

def redis_program(purpose, host, port, persisted_by_aof=False):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-'))),
            'resources': [('veil.backend.redis.redis_server_resource', {
                'purpose': purpose,
                'host': host,
                'port': port,
                'persisted_by_aof': persisted_by_aof
            })]
        }
    })

