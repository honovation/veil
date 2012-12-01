from __future__ import unicode_literals, print_function, division
import logging
import os
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None

@atomic_installer
def python_package_resource(name, version=None, **kwargs):
    pip_package = '{}=={}'.format(name, version) if version else name
    installed = is_python_package_installed(pip_package)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['python_package?{}'.format(pip_package)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing python package: %(pip_package)s ...', {'pip_package': pip_package})
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR', 'http://dependency-veil.googlecode.com/svn/trunk')
    if mirror:
        shell_execute('pip install {} --upgrade --no-index -f {}/'.format(pip_package, mirror), capture=True, **kwargs)
    else:
        shell_execute('pip install {} --upgrade'.format(pip_package), capture=True, **kwargs)


def is_python_package_installed(pip_package):
    global PIP_FREEZE_OUTPUT
    if not PIP_FREEZE_OUTPUT:
        PIP_FREEZE_OUTPUT = shell_execute('pip freeze', capture=True)
    return pip_package in PIP_FREEZE_OUTPUT