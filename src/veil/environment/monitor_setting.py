# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.redis_setting import redis_program


def monitor_programs(config):
    programs = merge_multiple_settings(
        redis_program('log_buffer', config.log_buffer_redis_host, config.log_buffer_redis_port,
                      snapshot_configs=[DictObject(interval=interval, changed_keys=changed_keys) for interval, changed_keys in
                                        [(900, 1), (300, 10), (60, 10000)]], recursive=True),
        {'elasticsearch': {
            'run_in_directory': '/usr/share/elasticsearch',
            'execute_command': '/usr/share/elasticsearch/bin/elasticsearch -Epath.conf={}/elasticsearch'.format(VEIL_ETC_DIR),
            'run_as': 'elasticsearch',
            'environment_variables': {'ES_JVM_OPTIONS': VEIL_ETC_DIR / 'elasticsearch/jvm.options'},
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'logstash': {
            'run_in_directory': '/usr/share/logstash',
            'execute_command': '/usr/share/logstash/bin/logstash --path.settings {}/logstash'.format(VEIL_ETC_DIR),
            'run_as': 'logstash',
            'environment_variables': {'HOME': os.environ.copy()['HOME']},
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }},
        {'kibana': {
            'run_in_directory': '/usr/share/kibana',
            'execute_command': '/usr/share/kibana/bin/kibana --host {}'.format(config.kibana_host),
            'run_as': 'kibana',
            'resources': [('veil.environment.monitor.elk_resource', {'config': config})]
        }}
    )
    return programs
