from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *
from veil_component import *
from .os_package_installer import os_package_resource

LOGGER = logging.getLogger(__name__)

@atomic_installer
def os_package_repository_resource(name):
    is_installed = is_os_package_repository_installed(name)
    action = None if is_installed else 'INSTALL'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['os_package_repository?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    LOGGER.info('installing os package repository: %(name)s ...', {'name': name})
    # install command add-apt-repository
    install_resource(os_package_resource(name='software-properties-common'))
    install_resource(os_package_resource(name='python-software-properties'))
    shell_execute('add-apt-repository ppa:{} -y'.format(name), capture=True)
    shell_execute('apt-get -q update', capture=True)


def is_os_package_repository_installed(name):
    ETC_APT = as_path('/etc/apt')
    if name in (ETC_APT / 'sources.list').text():
        return True
    for path in (ETC_APT / 'sources.list.d').files():
        if name in path.text():
            return True
    return False