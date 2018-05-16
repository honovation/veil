from __future__ import unicode_literals, print_function, division
import logging
from veil_component import as_path
from veil_installer import *
from veil.utility.shell import *
from .os_package_installer import os_package_resource

LOGGER = logging.getLogger(__name__)
ETC_APT = as_path('/etc/apt')


@atomic_installer
def apt_repository_resource(name, key_url, definition, version=None):
    install_apt_repository_resource(name, key_url, definition, version)


def install_apt_repository_resource(name, key_url, definition, version=None):
    installed = is_os_package_repository_installed(name, version)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['apt_repository?{}{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing apt repository: %(name)s, %(version)s ...', {'name': name, 'version': version})
    shell_execute('wget --inet4-only -q -O - {} | sudo apt-key add -'.format(key_url), capture=True)
    shell_execute('echo "{}" | sudo tee /etc/apt/sources.list.d/{}.list'.format(definition, name), capture=True)
    # apt update the added repository
    shell_execute('sudo apt update -o Dir::Etc::sourcelist="sources.list.d/{}.list" -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0"'.format(name),
                  capture=True, debug=True)


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
    # add the repository and apt update it
    shell_execute('sudo add-apt-repository ppa:{} -y -u'.format(name), capture=True)


def is_os_package_repository_installed(name, version=None):
    for path in (ETC_APT / 'sources.list.d').files():
        sources_list_d_content = path.text()
        if name in sources_list_d_content and (not version or version in sources_list_d_content):
            return True
    sources_list_content = (ETC_APT / 'sources.list').text()
    if name in sources_list_content and (not version or version in sources_list_content):
        return True
    return False
