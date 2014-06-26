from __future__ import unicode_literals, print_function, division
from veil_component import as_path
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.timer import *
from veil.utility.shell import *


@script('create-host-backup')
@log_elapsed_time
def create_host_backup(host_base_name, backup_dir, backup_file_template):
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
    check_servers_down(host_base_name)
    backup_dir.makedirs(0755)
    for dir_name, path in not_backed_up_subdir_name2path.items():
        shell_execute('tar -cpzf {} {} --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image'.format(path, dir_name),
            cwd=VEIL_VAR_DIR)


def check_servers_down(host_base_name):
    server_names = [server.name for server in list_veil_servers(VEIL_ENV_NAME) if server.mount_data_dir and server.host_base_name == host_base_name]
    if not server_names:
        return
    pattern = ' '.join('-e {}'.format(server_name) for server_name in server_names)
    try:
        shell_execute('ps -ef | grep supervisord | grep {} | grep {}'.format(VEIL_ETC_DIR.parent, pattern), capture=True)
    except ShellExecutionError:
        pass
    else:
        raise Exception('can not backup veil host while veil servers {} are running'.format(server_names))
