from __future__ import unicode_literals, print_function, division
import logging
from veil_component import as_path
from veil_installer import *
from veil.utility.shell import *
from .os_package_installer import os_package_resource, set_apt_get_update_executed

LOGGER = logging.getLogger(__name__)
ETC_APT = as_path('/etc/apt')


@atomic_installer
def apt_repository_resource(name, key_url, definition, version=None, update_apt_index=False):
    install_apt_repository_resource(name, key_url, definition, version)
    if update_apt_index:
        shell_execute('apt update -q')


def install_apt_repository_resource(name, key_url, definition, version=None):
    installed = is_os_package_repository_installed(name, version)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['apt_repository?{}{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing apt repository: %(name)s, %(version)s ...', {'name': name, 'version': version})
    add_apt_key_tried = 1
    while add_apt_key_tried <= 3:
        try:
            shell_execute('wget -q -O - {} | apt-key add -'.format(key_url), capture=True)
        except Exception as e:
            LOGGER.error('failed to add apt key: %(key_url)s, %(err)s', {'key_url': key_url, 'err': e.message})
            add_apt_key_tried += 1
        else:
            break
    shell_execute('echo "{}" | tee /etc/apt/sources.list.d/{}.list'.format(definition, name), capture=True)
    set_apt_get_update_executed(False)


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


def is_os_package_repository_installed(name, version=None):
    for path in (ETC_APT / 'sources.list.d').files():
        sources_list_d_content = path.text()
        if name in sources_list_d_content and (not version or version in sources_list_d_content):
            return True
    sources_list_content = (ETC_APT / 'sources.list').text()
    if name in sources_list_content and (not version or version in sources_list_content):
        return True
    return False
