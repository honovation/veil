from __future__ import unicode_literals, print_function, division
from veil_component import as_path
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *


@script('create-host-backup')
def create_host_backup(backup_dir, backup_file_template):
    backup_dir = as_path(backup_dir)
    backed_up = True
    not_backed_up_subdir_name2path = {}
    for subdir in VEIL_VAR_DIR.dirs():
        path = backup_dir / backup_file_template.format(subdir.name)
        if not path.exists():
            backed_up = False
            not_backed_up_subdir_name2path[subdir.name] = path
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['backup?{}'.format(backup_dir)] = '-' if backed_up else 'BACKUP'
        return
    if backed_up:
        return
    if is_any_server_running():
        raise Exception('can not backup veil host while not all veil servers on the host are down')
    backup_dir.makedirs(0755)
    for dir_name, path in not_backed_up_subdir_name2path.items():
        shell_execute('tar -czf {} {} -p -s --same-owner --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image'.format(
            path, dir_name), cwd=VEIL_VAR_DIR)


def is_any_server_running():
    try:
        shell_execute('ps -ef | grep supervisord | grep {} | grep -v -e @guard -e @monitor'.format(VEIL_ETC_DIR.parent), capture=True)
    except:
        return False
    else:
        return True
