# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)
LOGSTASH_MAJOR_VERSION = '1.4'
ELASTICSEARCH_MAJOR_VERSION = '1.1'
KIBANA_SOURCE_PATH = DEPENDENCY_DIR / 'kibana-latest.zip'
KIBANA_HOME = DEPENDENCY_INSTALL_DIR / 'kibana-latest'


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
    if KIBANA_SOURCE_PATH.exists():
        current_kibana_md5 = shell_execute('md5sum {}'.format(KIBANA_SOURCE_PATH), capture=True).split()[0]
    else:
        current_kibana_md5 = None
    try:
        shell_execute('wget -U "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36" -N http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip', cwd=KIBANA_SOURCE_PATH.parent, debug=True)
    except:  # workaround for wget gives 403 Forbidden
        if current_kibana_md5:
            new_kibana_md5 = current_kibana_md5
        else:
            raise
    else:
        new_kibana_md5 = shell_execute('md5sum {}'.format(KIBANA_SOURCE_PATH), capture=True).split()[0]
    if current_kibana_md5 != new_kibana_md5:
        LOGGER.info('installing new version of Kibana...')
        shell_execute('rm -rf kibana-latest', cwd=KIBANA_HOME.parent)
        shell_execute('unzip -o {}'.format(KIBANA_SOURCE_PATH), cwd=KIBANA_HOME.parent)
        if (KIBANA_HOME / 'app' / 'dashboards' / 'logstash.json').exists():
            shell_execute('mv -f logstash.json default.json', cwd=KIBANA_HOME / 'app' / 'dashboards')
    resources = [
        os_ppa_repository_resource(name='nginx/stable'),
        os_package_resource(name='nginx-extras'),
        os_service_resource(state='not_installed', name='nginx'),
        file_resource(path=VEIL_ETC_DIR / 'nginx.conf', content=render_config('nginx.conf.j2', kibana_root=KIBANA_HOME)),
        file_resource(path=KIBANA_HOME / 'config.js', content=render_config('kibana.config.js.j2', **config))
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
