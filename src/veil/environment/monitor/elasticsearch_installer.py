# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from .logstash_installer import oracle_java_resource

MAJOR_VERSION = '1.1'


@composite_installer
def elasticsearch_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        oracle_java_resource(),
        elasticsearch_apt_repository_resource(major_version=MAJOR_VERSION),
        os_package_resource(name='elasticsearch'),
        os_service_resource(state='not_installed', name='elasticsearch'),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch.yml',
            content=render_config('elasticsearch.yml.j2', log_dir=VEIL_LOG_DIR, data_dir=VEIL_VAR_DIR, elasticsearch_cluster=VEIL_ENV_NAME, **config)),
        file_resource(path=VEIL_ETC_DIR / 'logging.yml', content=render_config('logging.yml'))
    ])
    return resources
