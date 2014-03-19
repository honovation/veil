from __future__ import unicode_literals, print_function, division
import logging
from veil.env_const import VEIL_ENV_TYPE
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def os_package_resource(name):
    upgrade_mode = get_upgrade_mode()
    if upgrade_mode == UPGRADE_MODE_LATEST and VEIL_ENV_TYPE not in ('development', 'test'):
        raise Exception('please upgrade latest under development or test environment')

    installed_version, downloaded_version = get_local_os_package_versions(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    if UPGRADE_MODE_LATEST == upgrade_mode:
        may_update_resource_latest_version = VEIL_ENV_TYPE in ('development', 'test')
        need_install = None if installed_version else True
        need_download = True
        action = 'UPGRADE' if installed_version else 'INSTALL'
    elif UPGRADE_MODE_FAST == upgrade_mode:
        may_update_resource_latest_version = VEIL_ENV_TYPE in ('development', 'test') and not latest_version
        need_install = latest_version and latest_version != installed_version
        need_download = need_install and latest_version != downloaded_version
        if need_install:
            action = 'UPGRADE' if installed_version else 'INSTALL'
        else:
            action = None
    else:
        assert upgrade_mode == UPGRADE_MODE_NO
        may_update_resource_latest_version = need_install = need_download = False
        action = None

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if need_download and should_download_while_dry_run():
            new_downloaded_version = download_os_package(name, version=latest_version if UPGRADE_MODE_FAST == upgrade_mode else None)
            if new_downloaded_version != downloaded_version:
                LOGGER.warn('os package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version,
                    'new_downloaded_version': new_downloaded_version
                })
                downloaded_version = new_downloaded_version
            if UPGRADE_MODE_LATEST == upgrade_mode and action == 'UPGRADE' and installed_version == downloaded_version:
                action = None
        dry_run_result['os_package?{}'.format(name)] = action or '-'
        return

    if need_download:
        new_downloaded_version = download_os_package(name, version=latest_version if UPGRADE_MODE_FAST == upgrade_mode else None)
        if new_downloaded_version != downloaded_version:
            LOGGER.warn('os package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                'name': name,
                'installed_version': installed_version,
                'latest_version': latest_version,
                'downloaded_version': downloaded_version,
                'new_downloaded_version': new_downloaded_version
            })
            downloaded_version = new_downloaded_version
        if UPGRADE_MODE_LATEST == upgrade_mode and need_install is None:
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
        shell_execute('apt-get -y install {}={}'.format(name, downloaded_version), capture=True, debug=True)
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
    shell_execute('apt-get -y -d install {}{}'.format(name, '={}'.format(version) if version else ''), capture=True, debug=True)
    _, downloaded_version = get_local_os_package_versions(name)
    assert not version or version == downloaded_version, \
        'the downloaded version of os package {} is {}, different from the specific version {}'.format(name, downloaded_version, version)
    return downloaded_version


apt_get_update_executed = False

def update_os_package_catalogue():
    global apt_get_update_executed
    if not apt_get_update_executed:
        LOGGER.info('updating os package catalogue...')
        shell_execute('apt-get -q update', capture=True, debug=True)
        apt_get_update_executed = True


def to_resource_key(pip_package):
    return 'veil.server.os.os_package_resource?{}'.format(pip_package)


def get_local_os_package_versions(name):
    installed_version = None
    downloaded_version = None
    lines = shell_execute('apt-cache policy {}'.format(name), capture=True, debug=True).splitlines(False)
    if len(lines) >= 3:
        installed_version = lines[1].split('Installed:')[1].strip()
        if '(none)' == installed_version:
            installed_version = None
        downloaded_version = lines[2].split('Candidate:')[1].strip()
    return installed_version, downloaded_version
