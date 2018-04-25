# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import inotify.adapters
import inotify.constants
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *
from veil_component import VEIL_ENV, as_path

LOGGER = logging.getLogger(__name__)
SSH_KEY_PATH = '/etc/ssh/id_rsa-guard'


@script('snapshot-shipping')
def snapshot_shipping_script(purposes, remote_path):
    watch_directories = []
    for purpose in purposes.split(','):
        watch_directories.append(VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-')))

    monitor = inotify.adapters.Inotify()
    for directory in watch_directories:
        LOGGER.debug('watch directory: %(dir)s', {'dir': directory})
        monitor.add_watch(directory, mask=inotify.constants.IN_MOVED_TO)

    for event in monitor.event_gen():
        if event is None:
            continue
        (_, type_names, path, filename) = event

        if filename.endswith('.rdb'):
            LOGGER.debug('shipping to backup mirror: %(path)s, %(filename)s', {'path': path, 'filename': filename})
            shipping_to_backup_mirror('{}/{}'.format(path, filename), '{}/{}'.format(remote_path, filename))


def shipping_to_backup_mirror(source_path, remote_path):
    backup_mirror = get_current_veil_server().backup_mirror
    backup_mirror_path = '~/backup_mirror/{}/{}'.format(VEIL_ENV.name, remote_path)
    shell_execute(
        '''rsync -avhHPz -e "ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no" --numeric-ids --delete --bwlimit={} {} {}@{}:{}'''.format(
            SSH_KEY_PATH, backup_mirror.ssh_port, backup_mirror.bandwidth_limit, source_path, backup_mirror.ssh_user, backup_mirror.host_ip,
            backup_mirror_path), debug=True)


@script('bucket-shipping')
def bucket_shipping_script(exclude_buckets, remote_path):
    watch_directories = []
    exclude_buckets = exclude_buckets.split(',')
    for bucket_path in VEIL_BUCKETS_DIR.listdir():
        bucket_dir_name = bucket_path.basename()
        if bucket_dir_name not in exclude_buckets:
            watch_directories.append(bucket_path)

    mask = inotify.constants.IN_CREATE | inotify.constants.IN_MODIFY | inotify.constants.IN_DELETE | inotify.constants.IN_DELETE_SELF
    monitor = inotify.adapters.InotifyTrees(watch_directories, mask=mask)

    for event in monitor.event_gen():
        if event is None:
            continue
        (header, type_names, path, filename) = event
        print('{}/{} {}'.format(path, filename, type_names))
        if header.mask & inotify.constants.IN_IGNORED:
            continue
        if header.mask & (inotify.constants.IN_CREATE | inotify.constants.IN_ISDIR):
            continue
        if header.mask & (inotify.constants.IN_DELETE | inotify.constants.IN_ISDIR):
            continue
        if header.mask & (inotify.constants.IN_DELETE | inotify.constants.IN_DELETE_SELF):
            rel_path = VEIL_BUCKETS_DIR.relpathto(as_path(path).dirname())
        else:
            rel_path = VEIL_BUCKETS_DIR.relpathto(as_path(path) / filename)
        shipping_to_backup_mirror('{}/{}'.format(path, filename), '{}/{}'.format(remote_path, rel_path))
