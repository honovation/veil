# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.redis_setting import redis_program


def monitor_programs(config):
    programs = merge_multiple_settings(
        redis_program('log_buffer', config.log_buffer_redis_host, config.log_buffer_redis_port, snapshot_configs=[
            DictObject(interval=interval, changed_keys=changed_keys) for interval, changed_keys in [(900, 1), (300, 10), (60, 10000)]]),
        {'elasticsearch': {
            'environment_variables': {'ES_HEAP_SIZE': config.es_heap_size},
            'run_in_directory': '/usr/share/elasticsearch',
            'execute_command': '/usr/share/elasticsearch/bin/elasticsearch -Des.default.path.home=/usr/share/elasticsearch -Des.default.path.conf=/etc/elasticsearch -Des.default.path.logs=/var/log/elasticsearch -Des.default.path.data=/var/lib/elasticsearch -Des.default.path.work=/tmp/elasticsearch',
            'run_as': 'elasticsearch',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'logstash': {
            'environment_variables': {'LS_HEAP_SIZE': config.ls_heap_size},
            'run_in_directory': '/var/lib/logstash',
            'execute_command': '/opt/logstash/bin/logstash agent -f /etc/logstash/conf.d --allow-unsafe-shutdown',
            'run_as': 'logstash',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'kibana': {
            'run_in_directory': '/opt/kibana',
            'execute_command': '/opt/kibana/bin/kibana',
            'run_as': 'kibana',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }}
    )
    return programs

