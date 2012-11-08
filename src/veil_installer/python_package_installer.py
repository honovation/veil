from __future__ import unicode_literals, print_function, division
import logging
import os
from .shell import shell_execute
from .installer import installer

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None

def python_package_resource(name):
    return 'python_package', dict(name=name)

@installer('python_package')
def install_python_package(dry_run_result, name, **kwargs):
    installed = is_python_package_installed(name)
    if dry_run_result is not None:
        dry_run_result['python_package?{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing python package {} ...'.format(name))
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