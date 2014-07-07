# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.redis_setting import redis_program


def monitor_programs(config):
    programs = merge_multiple_settings(
        redis_program('log_buffer', config.log_buffer_redis_host, config.log_buffer_redis_port),
        {'logstash': {
            'execute_command': '/opt/logstash/bin/logstash agent -f {}/logstash.conf -v'.format(VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.logstash_resource', {'config': config})]
        }},
        {'elasticsearch': {
            'execute_command': '/usr/share/elasticsearch/bin/elasticsearch -Des.config={}/elasticsearch.yml'.format(VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.elasticsearch_resource', {'config': config})]
        }},
        {'nginx': {
            'execute_command': 'nginx -c {}/nginx.conf'.format(VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.kibana_resource', {'config': config})]
        }}
    )
    return programs