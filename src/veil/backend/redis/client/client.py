from __future__ import unicode_literals, print_function, division, absolute_import
from redis.client import Redis
from logging import getLogger
from veil.environment.setting import *
from veil.development.test import *

LOGGER = getLogger(__name__)

registry = {} # purpose => get_redis_options
instances = {} # purpose => instance (a.k.a Redis class instance)

def register_redis(purpose):
    if purpose not in registry:
        registry[purpose] = register_redis_options(purpose)
    return lambda: require_redis(purpose)


def register_redis_options(purpose):
    section = '{}_redis'.format(purpose) # for example cache_redis
    get_redis_host = register_option(section, 'host')
    get_redis_port = register_option(section, 'port', int)
    get_redis_password = register_option(section, 'password')

    def get_redis_options():
        return {
            'host': get_redis_host(),
            'port': get_redis_port(),
            'password': get_redis_password()
        }

    return get_redis_options


def require_redis(purpose):
    if purpose not in registry:
        raise Exception('redis for purpose {} is not registered'.format(purpose))
    if purpose not in instances:
        get_redis_options = registry[purpose]
        instances[purpose] = Redis(**get_redis_options())
    executing_test = get_executing_test(optional=True)
    if executing_test:
        executing_test.addCleanup(lambda :instances[purpose].flushall())
    return instances[purpose]
