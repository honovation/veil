from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def redis_program(purpose, host, port, persisted_by_aof=False, snapshot_configs=None):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-'))),
            'priority': 110,
            'stopwaitsecs': 60,
            'resources': [('veil.backend.redis.redis_server_source_code_resource', {
                'purpose': purpose,
                'host': host,
                'port': port,
                'persisted_by_aof': persisted_by_aof,
                'snapshot_configs': snapshot_configs
            })]
        }
    })
