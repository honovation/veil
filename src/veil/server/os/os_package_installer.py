from __future__ import unicode_literals, print_function, division
import logging
from veil.env_consts import VEIL_ENV_TYPE
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
apt_get_update_executed = False

@atomic_installer
def os_package_resource(name):
    installed_version, downloaded_version = get_local_os_package_versions(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    action = None if installed_version else 'INSTALL'
    upgrade_mode = get_upgrade_mode()
    if UPGRADE_MODE_LATEST == upgrade_mode:
        action = action or 'UPGRADE'
    elif UPGRADE_MODE_FAST == upgrade_mode:
        action = action or (None if latest_version == installed_version else 'UPGRADE')
    elif UPGRADE_MODE_NO == upgrade_mode:
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run():
            new_downloaded_version = download_os_package(name)
            if new_downloaded_version != downloaded_version:
                LOGGER.warn('os package with new version downloaded: %(name)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                    'name': name,
                    'downloaded_version': downloaded_version,
                    'new_downloaded_version': new_downloaded_version
                })
        dry_run_result['os_package?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    if UPGRADE_MODE_LATEST == upgrade_mode or (installed_version != latest_version and downloaded_version != latest_version):
        if UPGRADE_MODE_LATEST != upgrade_mode:
            LOGGER.debug('To download os package when upgrade mode is not latest: %(name)s, %(installed_version)s, %(downloaded_version)s, %(latest_version)s', {
                'name': name,
                'installed_version': installed_version,
                'downloaded_version': downloaded_version,
                'latest_version': latest_version
            })
        downloaded_version = download_os_package(name)
    if not installed_version or (UPGRADE_MODE_LATEST == upgrade_mode and (installed_version != downloaded_version or latest_version != downloaded_version)) or (UPGRADE_MODE_LATEST != upgrade_mode and installed_version != latest_version):
        LOGGER.info('installing os package: %(name)s ...', {'name': name})
        shell_execute('apt-get -y install {}'.format(name), capture=True)
        if downloaded_version != latest_version:
            if VEIL_ENV_TYPE in ('development', 'test'):
                set_resource_latest_version(to_resource_key(name), downloaded_version)
                LOGGER.info('os package upgraded to new version: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version
                })
            else:
                LOGGER.warn('OS PACKAGE UPGRADED TO A VERSION OTHER THAN LATEST VERSION: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version
                })


def download_os_package(name):
    LOGGER.info('downloading os package: %(name)s ...', {'name': name})
    update_os_package_catalogue()
    shell_execute('apt-get -y -d install {}'.format(name), capture=True)
    _, downloaded_version = get_local_os_package_versions(name)
    return downloaded_version


def update_os_package_catalogue():
    global apt_get_update_executed
    if not apt_get_update_executed:
        apt_get_update_executed = True
        LOGGER.info('updating os package catalogue...')
        shell_execute('apt-get -q update', capture=True)


def to_resource_key(pip_package):
    return 'veil.server.os.os_package_resource?{}'.format(pip_package)


def get_local_os_package_versions(name):
    installed_version = None
    downloaded_version = None
    lines = shell_execute('apt-cache policy {}'.format(name), capture=True).splitlines(False)
    if len(lines) >= 3:
        installed_version = lines[1].split('Installed:')[1].strip()
        if '(none)' == installed_version:
            installed_version = None
        downloaded_version = lines[2].split('Candidate:')[1].strip()
    return installed_version, downloaded_version
