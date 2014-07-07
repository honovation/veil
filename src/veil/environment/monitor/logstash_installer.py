# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

MAJOR_VERSION = '1.4'


@composite_installer
def logstash_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        oracle_java_resource(),
        logstash_apt_repository_resource(major_version=MAJOR_VERSION),
        os_package_resource(name='logstash'),
        os_service_resource(state='not_installed', name='logstash'),
        os_service_resource(state='not_installed', name='logstash-web'),
        file_resource(path=VEIL_ETC_DIR / 'logstash.conf', content=render_config('logstash.conf.j2', elasticsearch_cluster=VEIL_ENV_NAME, **config))
    ])
    return resources


@composite_installer
def oracle_java_resource():
    installer_package_name = 'oracle-java8-installer'
    shell_execute('echo {} shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections'.format(installer_package_name))
    resources = [
        os_ppa_repository_resource(name='webupd8team/java'),
        os_package_resource(name=installer_package_name)
    ]
    return resources
