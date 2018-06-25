from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def redis_program(purpose, host, port, max_memory=None, max_memory_policy=None, enable_aof=False, aof_fsync=None, enable_snapshot=True, snapshot_configs=()):
    return objectify({
        '{}_redis'.format(purpose): {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-'))),
            'priority': 110,
            'stopwaitsecs': 60,
            'resources': [('veil.backend.redis.redis_server_resource', {
                'purpose': purpose,
                'host': host,
                'port': port,
                'max_memory': max_memory,
                'max_memory_policy': max_memory_policy,
                'enable_aof': enable_aof,
                'aof_fsync': aof_fsync,
                'enable_snapshot': enable_snapshot,
                'snapshot_configs': snapshot_configs
            })]
        }
    })
