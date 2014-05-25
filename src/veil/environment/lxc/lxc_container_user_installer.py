from __future__ import unicode_literals, print_function, division
import subprocess
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def lxc_container_user_resource(container_name, user_name, state='created'):
    rootfs_path = '/var/lib/lxc/{}/rootfs'.format(container_name)
    try:
        is_user_existing = unsafe_call('chroot {} getent passwd {}'.format(rootfs_path, user_name))
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
    is_installed = group_name in unsafe_call('chroot {} groups {}'.format(rootfs_path, user_name))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_user_group?container_name={}&user_name={}&group_name={}'.format(container_name, user_name, group_name)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    unsafe_call('chroot {} usermod -a -G {} {}'.format(rootfs_path, group_name, user_name))


def unsafe_call(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output = process.communicate()[0]
    if process.returncode:
        raise Exception('failed to execute: {}'.format(command))
    return output


def lxc_container_sudoers_resource():
    pass