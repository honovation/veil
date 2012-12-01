from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def os_package_resource(name):
    installed = is_os_package_installed(name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['os_package?{}'.format(name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('installing os package: %(name)s ...', {'name': name})
    shell_execute('apt-get -y install {}'.format(name), capture=True)


def is_os_package_installed(name):
    try:
        shell_execute('dpkg -L {}'.format(name), capture=True)
        return True
    except ShellExecutionError, e:
        if 'not installed' in e.output:
            return False
        raise
