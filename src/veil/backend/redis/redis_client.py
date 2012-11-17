from __future__ import unicode_literals, print_function, division, absolute_import
from redis.client import Redis
from logging import getLogger
from veil.development.test import *
from veil.backend.redis_setting import get_redis_options

LOGGER = getLogger(__name__)

instances = {} # purpose => instance (a.k.a Redis class instance)

def register_redis(purpose):
    return lambda: require_redis(purpose)


def require_redis(purpose):
    redis_optiosn = get_redis_options(purpose)
    if purpose not in instances:
        instances[purpose] = Redis(**redis_optiosn)
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def flush():
            instances[purpose].flushall()
        executing_test.addCleanup(flush)
    return instances[purpose]
