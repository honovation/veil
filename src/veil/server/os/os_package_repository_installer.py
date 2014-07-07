from __future__ import unicode_literals, print_function, division
import logging
from veil_component import as_path, CURRENT_OS
from veil_installer import *
from veil.utility.shell import *
from .os_package_installer import os_package_resource, set_apt_get_update_executed

LOGGER = logging.getLogger(__name__)
ETC_APT = as_path('/etc/apt')
POSTGRESQL_APT_REPOSITORY_NAME = 'pgdg'
ELK_APT_REPOSITORY_NAME = 'elk'


@atomic_installer
def os_ppa_repository_resource(name):
    # add-apt-repository is in the package python-software-properties
    install_resource(os_package_resource(name='software-properties-common'))

    installed = is_os_package_repository_installed(name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['os_ppa_repository?{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing os package repository: %(name)s ...', {'name': name})
    shell_execute('add-apt-repository ppa:{} -y'.format(name), capture=True)
    set_apt_get_update_executed(False)


@atomic_installer
def postgresql_apt_repository_resource():
    installed = is_os_package_repository_installed(POSTGRESQL_APT_REPOSITORY_NAME)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_apt_repository?{}'.format(POSTGRESQL_APT_REPOSITORY_NAME)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing postgresql apt repository: %(name)s ...', {'name': POSTGRESQL_APT_REPOSITORY_NAME})
    shell_execute('echo "deb http://apt.postgresql.org/pub/repos/apt/ {os_codename}-{name} main" > /etc/apt/sources.list.d/{name}.list'.format(
        os_codename=CURRENT_OS.codename, name=POSTGRESQL_APT_REPOSITORY_NAME), capture=True)
    shell_execute('wget -q -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -', capture=True)
    set_apt_get_update_executed(False)


@atomic_installer
def elk_apt_repository_resource(elasticsearch_major_version, logstash_major_version):
    installed = is_os_package_repository_installed(ELK_APT_REPOSITORY_NAME, elasticsearch_major_version) and is_os_package_repository_installed(ELK_APT_REPOSITORY_NAME, logstash_major_version)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['elk_apt_repository?name={}&elasticsearch_major_version={}&logstash_major_version={}'.format(ELK_APT_REPOSITORY_NAME, elasticsearch_major_version, logstash_major_version)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing ELK apt repository: %(elasticsearch_major_version)s, %(logstash_major_version)s ...', {
        'elasticsearch_major_version': elasticsearch_major_version, 'logstash_major_version': logstash_major_version
    })
    shell_execute('wget -q -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | apt-key add -', capture=True)
    shell_execute('printf "deb http://packages.elasticsearch.org/elasticsearch/{}/debian stable main\ndeb http://packages.elasticsearch.org/logstash/{}/debian stable main" > /etc/apt/sources.list.d/{}.list'.format(
        elasticsearch_major_version, logstash_major_version, ELK_APT_REPOSITORY_NAME), capture=True)
    set_apt_get_update_executed(False)


def is_os_package_repository_installed(name, version=None):
    for path in (ETC_APT / 'sources.list.d').files():
        sources_list_d_content = path.text()
        if name in sources_list_d_content and (not version or version in sources_list_d_content):
            return True
    sources_list_content = (ETC_APT / 'sources.list').text()
    if name in sources_list_content and (not version or version in sources_list_content):
        return True
    return False
