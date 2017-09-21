from __future__ import unicode_literals, print_function, division, absolute_import

import socket
from logging import getLogger
from redis import StrictRedis
from veil_installer import *
from veil.development.test import *
from .redis_client_installer import redis_client_resource
from .redis_client_installer import redis_client_config

LOGGER = getLogger(__name__)

instances = {}  # (purpose, decode_responses) => instance (a.k.a Redis class instance)


def register_redis(purpose, decode_responses=True):
    add_application_sub_resource('{}_redis_client'.format(purpose), lambda config: redis_client_resource(purpose=purpose, **config))
    return lambda: require_redis(purpose, decode_responses)


def require_redis(purpose, decode_responses):
    key = (purpose, decode_responses)
    if key not in instances:
        config = redis_client_config(purpose)
        config['decode_responses'] = decode_responses
        config.setdefault('socket_connect_timeout', 3)
        config.setdefault('socket_timeout', None)
        config.setdefault('socket_keepalive', True)
        config.setdefault('socket_keepalive_options',
                          {socket.TCP_KEEPIDLE: 60, socket.TCP_KEEPINTVL: 15, socket.TCP_KEEPCNT: 8})
        instances[key] = StrictRedis(**config)
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def flush():
            instances[key].flushall()
        executing_test.addCleanup(flush)
    return instances[key]


def del_per_pattern(self, match, count=None):
    deleted_count = 0
    cursor = '0'
    while True:
        cursor, keys = self.scan(cursor, match, count)
        if not keys:
            break
        deleted_count += self.delete(*keys)
    return deleted_count


def hdel_per_pattern(self, key, match, count=None):
    deleted_count = 0
    cursor = '0'
    while True:
        cursor, fields = self.hscan(key, cursor, match, count)
        if not fields:
            break
        deleted_count += self.hdel(key, *fields)
    return deleted_count

StrictRedis.del_per_pattern = del_per_pattern
StrictRedis.hdel_per_pattern = hdel_per_pattern
