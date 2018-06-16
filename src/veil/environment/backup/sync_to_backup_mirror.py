# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment import VEIL_ENV, VEIL_BACKUP_MIRROR_ROOT, get_current_veil_server
from veil.utility.shell import *

SSH_KEY_PATH = '/etc/ssh/id_ed25519-guard'


def sync_to_backup_mirror(source_path, remote_path, base_path=None):
    server = get_current_veil_server()
    if not server.is_guard:
        raise AssertionError('only guard but not {} should be able to sync to backup mirror'.format(server.fullname))

    backup_mirror = server.backup_mirror
    backup_mirror_path = VEIL_BACKUP_MIRROR_ROOT / VEIL_ENV.name / server.host_base_name / remote_path
    ssh_option = 'ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no'.format(SSH_KEY_PATH, backup_mirror.ssh_port)
    shell_execute('rsync -avzhPH {} -e "{}" --rsync-path="mkdir -p {} && rsync" --numeric-ids --delete --bwlimit={} {} {}@{}:{}/'.format(
        '-R' if base_path else '', ssh_option, backup_mirror_path, backup_mirror.bandwidth_limit, source_path, backup_mirror.ssh_user, backup_mirror.host_ip,
        backup_mirror_path), debug=True, cwd=base_path)
