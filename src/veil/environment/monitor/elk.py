# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def elk_resource(config):
    repository_definition = 'deb https://artifacts.elastic.co/packages/5.x/apt stable main'
    return [
        oracle_java_resource(),
        apt_repository_resource(name='elk', key_url='https://artifacts.elastic.co/GPG-KEY-elasticsearch', definition=repository_definition),

        os_package_resource(name='elasticsearch'),
        file_resource(path='/etc/elasticsearch/elasticsearch.yml', keep_origin=True,
                      content=render_config('elasticsearch.yml.j2', elasticsearch_cluster=VEIL_ENV.name, **config)),

        os_package_resource(name='logstash'),
        file_resource(path='/etc/logstash/conf.d/10-logstash.conf', content=render_config('logstash.conf.j2', **config)),

        os_package_resource(name='kibana'),
    ]
