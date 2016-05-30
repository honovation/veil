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
            'execute_command': 'service elasticsearch start',
            'run_as': 'root',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'logstash': {
            'environment_variables': {'LS_HEAP_SIZE': config.ls_heap_size},
            'execute_command': 'service logstash restart',
            'run_as': 'root',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'kibana': {
            'execute_command': 'service kibana start',
            'run_as': 'root',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }}
    )
    return programs
