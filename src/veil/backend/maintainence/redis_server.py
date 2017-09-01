# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import logging

from redis.client import StrictRedis
from veil.environment import get_current_veil_env, get_current_veil_server
from veil.model.event import *
from veil.backend.job_queue import *
from veil.server.supervisor import *

LOGGER = logging.getLogger(__name__)


@task(queue='rewrite_redis_aof', schedule=cron_expr('47 * * * *'))
def rewrite_redis_aof():
    LOGGER.info('try to rewrite redis aof periodically')
    _rewrite_redis_aof()


@event(EVENT_SUPERVISOR_TO_BE_DOWN)
def rewrite_redis_aof():
    LOGGER.info('try to rewrite redis aof before supervisor shutdown')
    _rewrite_redis_aof(get_current_veil_server())


def _rewrite_redis_aof(veil_server=None):
    current_veil_env = get_current_veil_env()
    if not hasattr(current_veil_env.config, 'redis_servers'):
        return
    for host, port in current_veil_env.config.redis_servers:
        if veil_server and veil_server.internal_ip != host:
            continue
        client = StrictRedis(host=host, port=port)
        if client.config_get('appendonly')['appendonly'] != 'yes':
            continue
        LOGGER.info('rewrite redis aof <%(host)s:%(port)s>', {'host': host, 'port': port})
        client.bgrewriteaof()
