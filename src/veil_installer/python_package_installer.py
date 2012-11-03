from __future__ import unicode_literals, print_function, division
import logging
import os
from .shell import shell_execute

LOGGER = logging.getLogger(__name__)

def install_python_package(is_dry_run, name):
    installed = name in shell_execute('pip freeze', capture=True)
    if is_dry_run:
        return installed
    if installed:
        return
    LOGGER.info('installing python package {} ...'.format(name))
    mirror = os.getenv('VEIL_PYTHON_PACKAGE_MIRROR', 'http://dependency-veil.googlecode.com/svn/trunk/')
    # mirror = os.getenv('VEIL_PYTHON_PACKAGE_MIRROR', 'http://200.200.200.25:8080/')
    if mirror:
        shell_execute('pip install {} --no-index -f {}'.format(name, mirror), capture=True)
    else:
        shell_execute('pip install {}'.format(name), capture=True)

