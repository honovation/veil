# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def elk_resource(config):
    repository_definition = 'deb https://artifacts.elastic.co/packages/5.x/apt stable main'
    env = os.environ.copy()
    env['ES_SKIP_SET_KERNEL_PARAMETERS'] = 'true'
    return [
        os_package_resource(name='default-jre'),
        apt_repository_resource(name='elk', key_url='https://artifacts.elastic.co/GPG-KEY-elasticsearch', definition=repository_definition),
        os_package_resource(name='elasticsearch', install_env=env),
        directory_resource(path=VEIL_ETC_DIR / 'elasticsearch', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=VEIL_ETC_DIR / 'elasticsearch/scripts', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch/log4j2.properties', content=render_config('es_log4j2.properties'), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch/jvm.options',
                      content=render_config('es_jvm.options', min_heap_size=config.es_heap_size, max_heap_size=config.es_heap_size), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch/elasticsearch.yml',
                      content=render_config('elasticsearch.yml.j2', elasticsearch_cluster=VEIL_ENV.name, **config), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),

        directory_resource(path=VEIL_ETC_DIR / 'logstash', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=VEIL_ETC_DIR / 'logstash/conf.d', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        os_package_resource(name='logstash'),
        file_resource(path=VEIL_ETC_DIR / 'logstash/log4j2.properties', content=render_config('ls_log4j2.properties'), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'logstash/jvm.options',
                      content=render_config('ls_jvm.options', min_heap_size=config.ls_heap_size, max_heap_size=config.ls_heap_size), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'logstash/logstash.yml', content=render_config('logstash.yml', logstash_config_dir=VEIL_ETC_DIR / 'logstash/conf.d'),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'logstash/conf.d/10-logstash.conf', content=render_config('logstash.conf.j2', **config), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP),

        os_package_resource(name='kibana'),
    ]
