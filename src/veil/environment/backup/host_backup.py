from __future__ import unicode_literals, print_function, division
from veil_component import as_path
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *


@script('create-host-backup')
def create_host_backup(backup_path):
    backup_path = as_path(backup_path)
    backed_up = backup_path.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['backup?{}'.format(backup_path)] = '-' if backed_up else 'BACKUP'
        return
    if backed_up:
        return
    if is_any_servers_running():
        raise Exception('can not backup veil host while not all veil servers on the host are down')
    backup_path.parent.makedirs(0755)
    shell_execute('tar -czfps --same-owner {}  {} --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image'.format(backup_path,
        VEIL_VAR_DIR))


def is_any_servers_running():
    return bool(shell_execute('lxc-ps --lxc -ef | grep supervisord | grep -v -e @guard -e @monitor', capture=True))
