# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import OPT_DIR
from veil.profile.installer import *

LOGSTASH_CONF = VEIL_ETC_DIR / 'logstash.conf'
APT_SOURCES_LIST_DIR = as_path('/etc/apt/sources.list.d')


@composite_installer
def logstash_resource(config):
    if not (OPT_DIR / 'logstash-1.4.2.tar.gz').exists():
        shell_execute('wget https://download.elasticsearch.org/logstash/logstash/logstash-1.4.2.tar.gz', cwd=OPT_DIR)
    if not (OPT_DIR / 'logstash-1.4.2').exists():
        shell_execute('tar zxvf logstash-1.4.2.tar.gz', cwd=OPT_DIR)

    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_ppa_repository_resource(name='webupd8team/java'),
        os_package_resource(name='oracle-java7-installer'),
        file_resource(path=LOGSTASH_CONF, content=render_config('logstash.conf.j2', logs_redis_host=config.logs_redis_host,
            logs_redis_port=config.logs_redis_port, elasticsearch_host=config.elasticsearch_host, elasticsearch_port=config.elasticsearch_port))
    ])

    return resources
