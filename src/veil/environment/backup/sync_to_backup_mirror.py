# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import VEIL_BACKUP_MIRROR_ROOT
from veil.utility.shell import *

SSH_KEY_PATH = '/etc/ssh/id_ed25519-guard'


def sync_to_backup_mirror(backup_mirror, source_path, remote_path, base_path=None):
    backup_mirror_path = VEIL_BACKUP_MIRROR_ROOT / remote_path
    ssh_option = 'ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no'.format(SSH_KEY_PATH, backup_mirror.ssh_port)
    shell_execute('rsync -avzhPH {} -e "{}" --numeric-ids --delete --bwlimit={} {} {}@{}:{}'.format(
        '-R' if base_path else '', ssh_option, backup_mirror.bandwidth_limit, source_path, backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror_path
        ), debug=True, cwd=base_path)
