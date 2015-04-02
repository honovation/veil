from __future__ import unicode_literals, print_function, division
import logging
from veil_component import VEIL_ENV_TYPE
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def os_package_resource(name, cmd_run_before_install=None, cmd_run_if_install_fail=None, cmd_run_after_install=None):
    upgrading = is_upgrading()
    installed_version, downloaded_version = get_local_os_package_versions(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    if upgrading:
        may_update_resource_latest_version = VEIL_ENV_TYPE in {'development', 'test'}
        need_install = None if installed_version else True
        need_download = True
        action = 'UPGRADE' if installed_version else 'INSTALL'
    else:
        may_update_resource_latest_version = VEIL_ENV_TYPE in {'development', 'test'} and (not latest_version or latest_version < installed_version)
        need_install = not installed_version or latest_version and latest_version != installed_version
        need_download = need_install and (not downloaded_version or latest_version and latest_version != downloaded_version)
        if need_install:
            action = 'UPGRADE' if installed_version else 'INSTALL'
        else:
            action = None

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if need_download and is_downloading_while_dry_run():
            new_downloaded_version = download_os_package(name, version=None if upgrading else latest_version)
            if new_downloaded_version != downloaded_version:
                LOGGER.warn('os package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version,
                    'new_downloaded_version': new_downloaded_version
                })
                downloaded_version = new_downloaded_version
            if upgrading and action == 'UPGRADE' and installed_version == downloaded_version:
                action = None
        dry_run_result['os_package?{}'.format(name)] = action or '-'
        return

    if need_download:
        new_downloaded_version = download_os_package(name, version=None if upgrading else latest_version)
        if new_downloaded_version != downloaded_version:
            LOGGER.warn('os package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                'name': name,
                'installed_version': installed_version,
                'latest_version': latest_version,
                'downloaded_version': downloaded_version,
                'new_downloaded_version': new_downloaded_version
            })
            downloaded_version = new_downloaded_version
        if upgrading and need_install is None:
            need_install = installed_version != downloaded_version

    if need_install:
        if installed_version:
            LOGGER.info('upgrading os package: %(name)s, %(latest_version)s, %(installed_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'installed_version': installed_version,
                'version_to_install': downloaded_version
            })
        else:
            LOGGER.info('installing os package: %(name)s, %(latest_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'version_to_install': downloaded_version
            })
        if cmd_run_before_install:
            shell_execute(cmd_run_before_install, capture=True)
        try:
            shell_execute('apt-get -q -y install {}={}'.format(name, downloaded_version), capture=True, debug=True)
        except Exception:
            if cmd_run_if_install_fail:
                shell_execute(cmd_run_if_install_fail, capture=True)
        else:
            if cmd_run_after_install:
                shell_execute(cmd_run_after_install, capture=True)

        installed_version = downloaded_version

    if may_update_resource_latest_version and installed_version and installed_version != latest_version:
        set_resource_latest_version(to_resource_key(name), installed_version)
        LOGGER.info('updated os package resource latest version: %(name)s, %(latest_version)s, %(new_latest_version)s', {
            'name': name,
            'latest_version': latest_version,
            'new_latest_version': installed_version
        })


def download_os_package(name, version=None):
    LOGGER.info('downloading os package: %(name)s, %(version)s...', {'name': name, 'version': version})
    update_os_package_catalogue()
    shell_execute('apt-get -q -y -d install {}{}'.format(name, '={}'.format(version) if version else ''), capture=True, debug=True)
    _, downloaded_version = get_local_os_package_versions(name)
    assert not version or version == downloaded_version, \
        'the downloaded version of os package {} is {}, different from the specific version {}'.format(name, downloaded_version, version)
    return downloaded_version


apt_get_update_executed = False

def set_apt_get_update_executed(value):
    global apt_get_update_executed
    apt_get_update_executed = value


def update_os_package_catalogue():
    if not apt_get_update_executed:
        LOGGER.info('updating os package catalogue...')
        try:
            shell_execute('apt-get -q update', capture=True, debug=True)
        except ShellExecutionError:
            if VEIL_ENV_TYPE in {'development', 'test'}:
                LOGGER.exception('ignore the failure of running "apt-get update" under dev & test env.')
            else:
                raise
        set_apt_get_update_executed(True)


def to_resource_key(pip_package):
    return 'veil.server.os.os_package_resource?{}'.format(pip_package)


def get_local_os_package_versions(name):
    installed_version = None
    downloaded_version = None
    lines = shell_execute('apt-cache policy {}'.format(name), capture=True, debug=True).splitlines()
    if len(lines) >= 3:
        installed_version = lines[1].split('Installed:')[1].strip()
        if '(none)' == installed_version:
            installed_version = None
        downloaded_version = lines[2].split('Candidate:')[1].strip()
    return installed_version, downloaded_version
