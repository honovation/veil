from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def lxc_container_user_resource(container_name, user_name, state='created'):
    rootfs_path = '/var/lib/lxc/{}/rootfs'.format(container_name)
    try:
        is_user_existing = shell_execute('chroot {} getent passwd {}'.format(rootfs_path, user_name), capture=True)
    except:
        is_user_existing = False
    if 'created' == state:
        action = '-' if is_user_existing else 'CREATE'
    elif 'deleted' == state:
        action = 'DELETE' if is_user_existing else '-'
    else:
        raise Exception('unknown state: {}'.format(state))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_user?container_name={}&user_name={}'.format(container_name, user_name)
        dry_run_result[key] = action
        return
    if 'CREATE' == action:
        LOGGER.info('create lxc container user: %(user_name)s in container %(container_name)s...', {
            'user_name': user_name,
            'container_name': container_name
        })
        shell_execute('chroot {} useradd --create-home -s /bin/bash {}'.format(rootfs_path, user_name), capture=True)
    elif 'DELETE' == action:
        LOGGER.info('delete lxc container user: %(user_name)s in container %(container_name)s...', {
            'user_name': user_name,
            'container_name': container_name
        })
        shell_execute('chroot {} userdel -r {}'.format(rootfs_path, user_name), capture=True)



@atomic_installer
def lxc_container_user_group_resource(container_name, user_name, group_name):
    rootfs_path = '/var/lib/lxc/{}/rootfs'.format(container_name)
    is_installed = group_name in shell_execute('chroot {} groups {}'.format(rootfs_path, user_name), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_user_group?container_name={}&user_name={}&group_name={}'.format(container_name, user_name, group_name)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    shell_execute('chroot {} usermod -a -G {} {}'.format(rootfs_path, group_name, user_name), capture=True)
