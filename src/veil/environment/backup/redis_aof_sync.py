# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from .sync_to_backup_mirror import sync_to_backup_mirror

LOGGER = logging.getLogger(__name__)


@script('redis-aof-sync')
def sync_redis_aof_script(purposes, remote_path, crontab_expression):
    @run_every(crontab_expression)
    def sync_redis_aof(redis_directories):
        for directory in redis_directories:
            rel_path = VEIL_DATA_DIR.relpathto('{}/appendonly.aof'.format(directory))
            sync_to_backup_mirror(backup_mirror, rel_path, remote_path, VEIL_DATA_DIR)

    directories = []
    for purpose in purposes.split(','):
        directories.append(VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-')))

    backup_mirror = get_current_veil_server().backup_mirror
    sync_redis_aof(backup_mirror, directories)
