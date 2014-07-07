# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

MAJOR_VERSION = '1.1'


@composite_installer
def elasticsearch_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    shell_execute('echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
    resources.extend([
        os_ppa_repository_resource(name='webupd8team/java'),
        os_package_resource(name='oracle-java8-installer'),
        elasticsearch_apt_repository_resource(major_version=MAJOR_VERSION),
        os_package_resource(name='elasticsearch'),
        os_service_resource(state='not_installed', name='elasticsearch'),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch.yml',
            content=render_config('elasticsearch.yml.j2', log_dir=VEIL_LOG_DIR, data_dir=VEIL_VAR_DIR, elasticsearch_cluster=VEIL_ENV_NAME, **config))
    ])
    return resources
