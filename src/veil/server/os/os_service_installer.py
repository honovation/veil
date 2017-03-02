from __future__ import unicode_literals, print_function, division
import logging

from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def os_service_auto_starting_resource(name, state):
    if 'not_installed' != state:
        raise NotImplementedError('only support remove os service')
    installed = is_service_auto_starting_installed(name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['os_service?{}'.format(name)] = 'UNINSTALL' if installed else '-'
        return
    if installed:
        LOGGER.info('uninstall os service: %(name)s', {'name': name})
        stop_service(name)
        disable_auto_starting(name)


def stop_service(name):
    try_shell_execute('systemctl stop {}'.format(name))


def is_service_auto_starting_installed(name):
    return try_shell_execute('systemctl is-enabled {}'.format(name), capture=True) in {'enabled', 'static'}


def disable_auto_starting(name):
    try_shell_execute('systemctl disable {}'.format(name))
