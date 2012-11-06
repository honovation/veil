from __future__ import unicode_literals, print_function, division
import os
import logging
from .shell import shell_execute
from .installer import installer

LOGGER = logging.getLogger(__name__)

def os_service_resource(name, path, state):
    return 'os_service', dict(name=name, path=path, state=state)


@installer('os_service')
def install_os_service(dry_run_result, name, path, state):
    if 'not_installed' != state:
        raise NotImplementedError('only support remove os service')
    installed = os.path.exists(path)
    if dry_run_result is not None:
        dry_run_result['os_service?{}'.format(name)] = 'UNINSTALL' if installed else '-'
        return
    if installed:
        LOGGER.info('uninstall os service {} from {}'.format(name, path))
        shell_execute('service {} stop'.format(name), capture=True)
        shell_execute('update-rc.d -f {} remove'.format(name), capture=True)