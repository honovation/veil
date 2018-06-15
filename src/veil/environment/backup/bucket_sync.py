# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import inotify.adapters
import inotify.constants
from veil.environment import *
from veil.frontend.cli import *
from veil_component import as_path
from .sync_to_backup_mirror import sync_to_backup_mirror

LOGGER = logging.getLogger(__name__)


@script('bucket-sync')
def sync_bucket_script(exclude_buckets, remote_path):
    watch_directories = []
    exclude_buckets = exclude_buckets.split(',')
    for bucket_path in VEIL_BUCKETS_DIR.listdir():
        bucket_dir_name = bucket_path.basename()
        if bucket_dir_name not in exclude_buckets:
            LOGGER.info('watching bucket directory: %(bucket_path)s', {'bucket_path': bucket_path})
            watch_directories.append(bucket_path)

    mask = inotify.constants.IN_CREATE | inotify.constants.IN_MODIFY | inotify.constants.IN_DELETE | inotify.constants.IN_DELETE_SELF | inotify.constants.IN_MOVED_TO
    monitor = inotify.adapters.InotifyTrees(watch_directories, mask=mask)

    backup_mirror = get_current_veil_env().backup_mirror
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
        sync_to_backup_mirror(backup_mirror, rel_path, remote_path, VEIL_BUCKETS_DIR)
