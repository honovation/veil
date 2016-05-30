from __future__ import unicode_literals, print_function, division
import glob
import os
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
        try_shell_execute('update-rc.d {} disable'.format(name), capture=True)
        try_shell_execute('sh -c "echo manual > /etc/init/{}.override"'.format(name))


def stop_service(name):
    try_shell_execute('service {} stop'.format(name), capture=True)


def is_service_auto_starting_installed(name):
    return any(glob.glob('/etc/rc{}.d/S[1-9][0-9]{}'.format(i, name)) for i in range(7)) or (
        os.path.exists('/etc/init/{}.conf'.format(name)) and not os.path.exists('/etc/init/{}.override'.format(name))
    )
