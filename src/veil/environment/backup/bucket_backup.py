# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import inotify.adapters
import inotify.constants
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *
from veil_component import as_path

LOGGER = logging.getLogger(__name__)
SSH_KEY_PATH = '/etc/ssh/id_rsa-guard'


def shipping_to_backup_mirror(source_path, remote_path, cwd):
    backup_mirror = get_current_veil_server().backup_mirror
    backup_mirror_path = '~/backup_mirror/{}'.format(remote_path)
    ssh_option = 'ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no'.format(SSH_KEY_PATH, backup_mirror.ssh_port)
    shell_execute('rsync -avzhPR -e "{}" --numeric-ids --delete --bwlimit={} {} {}@{}:{}'.format(ssh_option, backup_mirror.bandwidth_limit, source_path,
                                                                                                 backup_mirror.ssh_user, backup_mirror.host_ip,
                                                                                                 backup_mirror_path), debug=True, cwd=cwd)


@script('bucket-shipping')
def bucket_shipping_script(exclude_buckets, remote_path):
    watch_directories = []
    exclude_buckets = exclude_buckets.split(',')
    for bucket_path in VEIL_BUCKETS_DIR.listdir():
        bucket_dir_name = bucket_path.basename()
        if bucket_dir_name not in exclude_buckets:
            LOGGER.info('watching bucket directory: %(bucket_path)s', {'bucket_path': bucket_path})
            watch_directories.append(bucket_path)

    mask = inotify.constants.IN_CREATE | inotify.constants.IN_MODIFY | inotify.constants.IN_DELETE | inotify.constants.IN_DELETE_SELF | inotify.constants.IN_MOVED_TO
    monitor = inotify.adapters.InotifyTrees(watch_directories, mask=mask)

    for event in monitor.event_gen():
        if event is None:
            continue
        (header, type_names, path, filename) = event
        if header.mask & inotify.constants.IN_IGNORED:
            continue
        if header.mask & inotify.constants.IN_DELETE_SELF:
            continue
        if filename.startswith('tmp') and filename.endswith('---tmp'):
            continue
        if header.mask & inotify.constants.IN_DELETE and header.mask & inotify.constants.IN_ISDIR:
            rel_path = VEIL_BUCKETS_DIR.relpathto(path)
        else:
            if (as_path(path) / filename).exists():
                rel_path = VEIL_BUCKETS_DIR.relpathto(as_path(path) / filename)
            else:
                rel_path = VEIL_BUCKETS_DIR.relpathto(path)
        shipping_to_backup_mirror(rel_path, remote_path, VEIL_BUCKETS_DIR)
