from __future__ import unicode_literals, print_function, division
import logging
import os
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None

@atomic_installer
def python_package_resource(name, url=None, **kwargs):
    pip_package = name
    action = None if is_python_package_installed(pip_package) else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        raise NotImplementedError()
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['python_package?{}'.format(pip_package)] = action or '-'
        return
    if not action:
        return
    LOGGER.info('installing python package: %(pip_package)s ...', {'pip_package': pip_package})
    pip_arg = ''
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR')
    if mirror:
        pip_arg = '--no-index -f {}:8080'.format(mirror)
    if 'UPGRADE' == action:
        pip_arg = '{} --upgrade'.format(pip_arg)
    shell_execute('pip install {} {}'.format(url if url else pip_package, pip_arg), capture=True, **kwargs)


def is_python_package_installed(pip_package):
    global PIP_FREEZE_OUTPUT
    if not PIP_FREEZE_OUTPUT:
        PIP_FREEZE_OUTPUT = shell_execute('pip freeze', capture=True)
    return pip_package in PIP_FREEZE_OUTPUT