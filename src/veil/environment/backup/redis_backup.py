# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *
from veil.utility.timer import *

LOGGER = logging.getLogger(__name__)
SSH_KEY_PATH = '/etc/ssh/id_ed25519-guard'


@script('aof-shipping')
def aof_shipping_script(purposes, remote_path, crontab_expression):
    @run_every(crontab_expression)
    def backup_redis_aof(redis_directories):
        for directory in redis_directories:
            rel_path = VEIL_DATA_DIR.relpathto('{}/appendonly.aof'.format(directory))
            shipping_to_backup_mirror(rel_path, remote_path, VEIL_DATA_DIR)

    directories = []
    for purpose in purposes.split(','):
        directories.append(VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-')))

    backup_redis_aof(directories)


def shipping_to_backup_mirror(source_path, remote_path, cwd):
    backup_mirror = get_current_veil_server().backup_mirror
    backup_mirror_path = '~/backup_mirror/{}'.format(remote_path)
    ssh_option = 'ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no'.format(SSH_KEY_PATH, backup_mirror.ssh_port)
    shell_execute('rsync -avzhPR -e "{}" --numeric-ids --delete --bwlimit={} {} {}@{}:{}'.format(ssh_option, backup_mirror.bandwidth_limit, source_path,
                                                                                                 backup_mirror.ssh_user, backup_mirror.host_ip,
                                                                                                 backup_mirror_path), debug=True, cwd=cwd)
