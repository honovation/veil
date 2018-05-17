from __future__ import unicode_literals, print_function, division

import glob
import logging
import os

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
    try_shell_execute('sudo systemctl stop {}'.format(name))
    try_shell_execute('sudo service {} stop'.format(name))


def is_service_auto_starting_installed(name):
    return try_shell_execute('sudo systemctl is-enabled {}'.format(name), capture=True, expected_return_codes=(0, 1)) == 'enabled' \
           or any(glob.glob('/etc/rc{}.d/S[0-9][0-9]{}'.format(i, name)) for i in range(7)) \
           or (os.path.exists('/etc/init/{}.conf'.format(name)) and not os.path.exists('/etc/init/{}.override'.format(name)))


def disable_auto_starting(name):
    try_shell_execute('sudo systemctl disable {}'.format(name))
    try_shell_execute('sudo update-rc.d {} disable'.format(name))
    try_shell_execute('sudo mkdir -p /etc/init')
    try_shell_execute('echo manual | sudo tee /etc/init/{}.override'.format(name))
