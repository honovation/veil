from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
apt_get_update_executed = False

@atomic_installer
def os_package_resource(name):
    installed_version = get_os_package_installed_version(name)
    action = None if installed_version else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        latest_version = get_resource_latest_version(to_resource_key(name))
        action = None if latest_version == installed_version else 'UPGRADE'
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run():
            download_os_package(name)
        dry_run_result['os_package?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    if 'UPGRADE' == action:
        download_os_package(name)
    LOGGER.info('installing os package: %(name)s ...', {'name': name})
    shell_execute('apt-get -y install {}'.format(name), capture=True)
    package_version = get_os_package_installed_version(name)
    set_resource_latest_version(to_resource_key(name), package_version)


def download_os_package(name):
    LOGGER.info('downloading os package: %(name)s ...', {'name': name})
    global apt_get_update_executed
    if not apt_get_update_executed:
        apt_get_update_executed = True
        LOGGER.info('updating os package catalogue...')
        shell_execute('apt-get update -q', capture=True)
    shell_execute('apt-get -d install {}'.format(name), capture=True)


def to_resource_key(pip_package):
    return 'veil.server.os.os_package_resource?{}'.format(pip_package)


def get_os_package_installed_version(name):
    try:
        lines = shell_execute('dpkg -s {}'.format(name), capture=True).splitlines(False)
        for line in lines:
            if line.startswith('Version:'):
                return line.split('Version:')[1].strip()
        return None
    except ShellExecutionError, e:
        if 'not installed' in e.output:
            return None
        raise
