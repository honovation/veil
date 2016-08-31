# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from redis.client import StrictRedis
from veil.environment import get_current_veil_env
from veil.backend.queue import *


@periodic_job('17 1 * * 0')
def rewrite_redis_aof_job():
    current_veil_env = get_current_veil_env()
    if not hasattr(current_veil_env.config, 'redis_servers'):
        return
    for host, port in current_veil_env.config.redis_servers:
        client = StrictRedis(host=host, port=port)
        if client.config_get('appendonly')['appendonly'] != 'yes':
            continue
        client.bgrewriteaof()
