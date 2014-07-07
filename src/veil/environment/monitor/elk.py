# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import OPT_DIR
from veil.profile.installer import *

LOGSTASH_MAJOR_VERSION = '1.4'
ELASTICSEARCH_MAJOR_VERSION = '1.1'
KIBANA_DIR = OPT_DIR / 'kibana-latest'


@composite_installer
def logstash_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        oracle_java_resource(),
        elk_apt_repository_resource(elasticsearch_major_version=ELASTICSEARCH_MAJOR_VERSION, logstash_major_version=LOGSTASH_MAJOR_VERSION),
        os_package_resource(name='logstash'),
        os_service_resource(state='not_installed', name='logstash'),
        os_service_resource(state='not_installed', name='logstash-web'),
        file_resource(path=VEIL_ETC_DIR / 'logstash.conf', content=render_config('logstash.conf.j2', elasticsearch_cluster=VEIL_ENV_NAME, **config))
    ])
    return resources


@composite_installer
def elasticsearch_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        oracle_java_resource(),
        elk_apt_repository_resource(elasticsearch_major_version=ELASTICSEARCH_MAJOR_VERSION, logstash_major_version=LOGSTASH_MAJOR_VERSION),
        os_package_resource(name='elasticsearch'),
        os_service_resource(state='not_installed', name='elasticsearch'),
        file_resource(path=VEIL_ETC_DIR / 'elasticsearch.yml', content=render_config('elasticsearch.yml.j2', log_dir=VEIL_LOG_DIR,
            data_dir=VEIL_VAR_DIR, elasticsearch_cluster=VEIL_ENV_NAME, **config)),
        file_resource(path=VEIL_ETC_DIR / 'logging.yml', content=render_config('logging.yml'))
    ])
    return resources


@composite_installer
def kibana_resource(config):
    if not (OPT_DIR / 'kibana-latest.zip').exists():
        shell_execute('wget http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip', cwd=OPT_DIR)
    else:
        current_kibana_md5 = shell_execute('md5sum kibana-latest.zip', cwd=OPT_DIR, capture=True).split()[0]
        shell_execute('wget -N http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip', cwd=OPT_DIR)
        new_kibana_md5 = shell_execute('md5sum kibana-latest.zip', cwd=OPT_DIR, capture=True).split()[0]
        if current_kibana_md5 != new_kibana_md5:
            shell_execute('rm -rf kibana-latest', cwd=OPT_DIR)
        else:
            print('no change for kibana-latest')
            return
    shell_execute('unzip -o kibana-latest.zip', cwd=OPT_DIR)
    if (KIBANA_DIR / 'app/dashboards/logstash.json').exists():
        shell_execute('mv logstash.json default.json', cwd=KIBANA_DIR / 'app/dashboards')

    resources = [
        os_ppa_repository_resource(name='nginx/stable'),
        os_package_resource(name='nginx-extras'),
        os_service_resource(state='not_installed', name='nginx'),
        file_resource(path=VEIL_ETC_DIR / 'nginx.conf', content=render_config('nginx.conf.j2', kibana_root=KIBANA_DIR)),
        file_resource(path=KIBANA_DIR / 'config.js', content=render_config('kibana.config.js.j2', **config))
    ]
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
