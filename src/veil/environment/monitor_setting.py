# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import OPT_DIR
from veil.profile.installer import *


def monitor_program(config):
    return objectify({
        'nginx': {
            'execute_command': 'nginx -c {}/nginx.conf'.format(VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.kibana_resource', {})]
        },
        'elasticsearch': {
            'execute_command': '{}/elasticsearch-1.1.1/bin/elasticsearch -Des.config={}/elasticsearch.yml'.format(OPT_DIR, VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.elasticsearch_resource', {'config': config})]
        },
        'logstash': {
            'execute_command': '{}/logstash-1.4.2/bin/logstash agent -f {}/logstash.conf -v'.format(OPT_DIR, VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.logstash_resource', {'config': config})]
        },
        'log-redis': {
            'execute_command': 'redis-server {}'.format(VEIL_ETC_DIR / 'logs-redis.conf'),
            'run_as': 'root',
            'resources': [('veil.backend.redis.redis_server_resource', {
                'purpose': 'logs',
                'host': config.logs_redis_host,
                'port': config.logs_redis_port
            })]
        }
    })