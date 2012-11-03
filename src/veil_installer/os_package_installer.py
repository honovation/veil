from __future__ import unicode_literals, print_function, division
import logging
from .shell import shell_execute
from .shell import ShellExecutionError

LOGGER = logging.getLogger(__name__)

def install_os_package(is_dry_run, name):
    installed = is_os_package_installed(name)
    if is_dry_run:
        return installed
    if installed:
        return
    LOGGER.info('installing os package {} ...'.format(name))
    shell_execute('apt-get -y install {}'.format(name), capture=True)


def is_os_package_installed(name):
    try:
        shell_execute('dpkg -L {}'.format(name), capture=True)
        return True
    except ShellExecutionError, e:
        if 'not installed' in e.output:
            return False
        raise