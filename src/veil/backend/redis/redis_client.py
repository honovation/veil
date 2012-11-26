from __future__ import unicode_literals, print_function, division, absolute_import
from redis.client import Redis
from logging import getLogger
from veil_installer import *
from veil.development.test import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

LOGGER = getLogger(__name__)

instances = {} # purpose => instance (a.k.a Redis class instance)

def register_redis(purpose):
    return lambda: require_redis(purpose)


def require_redis(purpose):
    if purpose not in instances:
        redis_client_config = load_redis_client_config(purpose)
        instances[purpose] = Redis(**redis_client_config)
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def flush():
            instances[purpose].flushall()

        executing_test.addCleanup(flush)
    return instances[purpose]


@composite_installer('redis_client')
def install_redis_client(purpose, host, port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')), content=render_config(
            'redis-client.cfg.j2', host=host, port=port)))
    return [], resources


def load_redis_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-redis-client.cfg'.format(purpose.replace('_', '-')), 'host', 'port')
    config.port = int(config.port)
    return config