# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.redis_setting import redis_program


def monitor_programs(config):
    programs = merge_multiple_settings(
        redis_program('log_buffer', config.log_buffer_redis_host, config.log_buffer_redis_port, snapshot_configs=[
            DictObject(interval=interval, changed_keys=changed_keys) for interval, changed_keys in [(900, 1), (300, 10), (60, 10000)]]),
        {'logstash': {
            'environment_variables': 'LS_HEAP_SIZE={}'.format(config.ls_heap_size),
            'execute_command': '/opt/logstash/bin/logstash agent -f {}/logstash.conf -v'.format(VEIL_ETC_DIR),
            'run_as': 'root',
            'resources': [('veil.environment.monitor.logstash_resource', {'config': config})]
        }},
        {'elasticsearch': {
            'environment_variables': 'ES_HEAP_SIZE={}'.format(config.es_heap_size),
            'execute_command': '/usr/share/elasticsearch/bin/elasticsearch -Des.path.conf={}'.format(VEIL_ETC_DIR),
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
