from __future__ import unicode_literals, print_function, division
import logging
import re
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None

@atomic_installer
def python_package_resource(name, url=None, **kwargs):
    installed_version = get_python_package_installed_version(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    action = None if installed_version else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = action or 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        action = action or None if latest_version == installed_version else 'UPGRADE'
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run():
            download_python_package(name)
        dry_run_result['python_package?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    download_python_package(name)
    LOGGER.info('installing python package: %(name)s ...', {'name': name})
    pip_arg = '--upgrade' if 'UPGRADE' == action else ''
    shell_execute('pip install {} {}'.format(url if url else name, pip_arg),
        capture=True, **kwargs)
    package_version = get_python_package_installed_version(name, from_cache=False)
    set_resource_latest_version(to_resource_key(name), package_version)


def download_python_package(name):
    LOGGER.info('downloading python package: %(name)s ...', {'name': name})
    shell_execute('pip install {} --no-install'.format(name))


def to_resource_key(pip_package):
    return 'veil.server.python.python_package_resource?{}'.format(pip_package)


def get_python_package_installed_version(pip_package, from_cache=True):
    global PIP_FREEZE_OUTPUT
    if not from_cache:
        PIP_FREEZE_OUTPUT = None
    if not PIP_FREEZE_OUTPUT:
        PIP_FREEZE_OUTPUT = shell_execute('pip freeze', capture=True)
    lines = PIP_FREEZE_OUTPUT.splitlines(False)
    for line in lines:
        match = re.match('{}==(.*)'.format(pip_package), line)
        if match:
            return match.group(1)
    return None