from __future__ import unicode_literals, print_function, division
import os
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def os_service_resource(name, path, state):
    if 'not_installed' != state:
        raise NotImplementedError('only support remove os service')
    installed = os.path.exists(path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['os_service?{}'.format(name)] = 'UNINSTALL' if installed else '-'
        return
    if installed:
        LOGGER.info('uninstall os service: %(name)s from %(path)s', {
            'name': name,
            'path': path
        })
        stop_service(name)
        shell_execute('update-rc.d -f {} disable'.format(name), capture=True)
    if UPGRADE_MODE_NO != get_upgrade_mode():
    # some upgrade will restart the service
        stop_service(name)


def stop_service(name):
    try:
        shell_execute('service {} stop'.format(name), capture=True)
    except:
        pass