from __future__ import unicode_literals, print_function, division
import logging
import os
from .shell import shell_execute
from .installer import atomic_installer
from .installer import get_dry_run_result

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None

@atomic_installer
def python_package_resource(name, **kwargs):
    installed = is_python_package_installed(name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['python_package?{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing python package: %(name)s ...', {'name': name})
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR', 'http://dependency-veil.googlecode.com/svn/trunk')
    if mirror:
        shell_execute('pip install {} --no-index -f {}/'.format(name, mirror), capture=True, **kwargs)
    else:
        shell_execute('pip install {}'.format(name), capture=True, **kwargs)


def is_python_package_installed(name):
    global PIP_FREEZE_OUTPUT
    if not PIP_FREEZE_OUTPUT:
        PIP_FREEZE_OUTPUT = shell_execute('pip freeze', capture=True)
    return name in PIP_FREEZE_OUTPUT