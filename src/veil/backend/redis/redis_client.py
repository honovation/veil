from __future__ import unicode_literals, print_function, division, absolute_import
from logging import getLogger
from redis.client import StrictRedis
from veil_installer import *
from veil.development.test import *
from .redis_client_installer import redis_client_resource
from .redis_client_installer import redis_client_config

LOGGER = getLogger(__name__)

instances = {} # purpose => instance (a.k.a Redis class instance)

def register_redis(purpose):
    add_application_sub_resource('{}_redis_client'.format(purpose), lambda config: redis_client_resource(purpose=purpose, **config))
    return lambda: require_redis(purpose)


def require_redis(purpose):
    if purpose not in instances:
        config = redis_client_config(purpose)
        instances[purpose] = StrictRedis(**config)
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def flush():
            instances[purpose].flushall()
        executing_test.addCleanup(flush)
    return instances[purpose]


def delete_per_pattern(self, pattern, batch_size=1000):
    count = 0
    cursor = '0'
    while True:
        cursor, keys = self.scan(cursor, pattern, batch_size)
        if not keys:
            break
        count += self.delete(*keys)
    return count


StrictRedis.delete_per_pattern = delete_per_pattern
