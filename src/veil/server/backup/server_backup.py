from __future__ import unicode_literals, print_function, division
import os
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.server.supervisor import *
from veil.utility.shell import *


@script('create')
def create_server_backup(backup_path):
    is_backup_there = os.path.exists(backup_path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['backup?{}'.format(backup_path)] = '-' if is_backup_there else 'BACKUP'
        return
    if is_backup_there:
        return
    if is_supervisord_running():
        raise Exception('can not backup while supervisord is executing')
    backup_to_dir = os.path.dirname(backup_path)
    if not os.path.exists(backup_to_dir):
        os.makedirs(backup_to_dir, mode=0755)
    backup_dirs = get_current_veil_server().backup_dirs
    backup_dir_list = [VEIL_VAR_DIR] if not backup_dirs else [VEIL_VAR_DIR] + backup_dirs
    shell_execute('tar czf {} --exclude=*.pid --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image {}'.format(
        backup_path, ' '.join(backup_dir_list)
    ))