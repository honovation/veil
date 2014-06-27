from __future__ import unicode_literals, print_function, division
import fabric.api
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
    backup_dir.makedirs(0755)
    for dir_name, path in not_backed_up_subdir_name2path.items():
        try:
            if VEIL_DATA_DIR.name == dir_name:
                servers_to_down = [s for s in list_veil_servers(VEIL_ENV_NAME) if s.mount_data_dir and s.host_base_name == host_base_name]
                for server in servers_to_down:
                    bring_down_server(server)
            shell_execute('tar -cpzf {} {} --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image'.format(path, dir_name),
                cwd=VEIL_VAR_DIR)
        finally:
            if VEIL_DATA_DIR.name == dir_name:
                for server in servers_to_down:
                    bring_up_server(server)


def bring_down_server(server):
    with fabric.api.settings(host_string=server.deploys_via, disable_known_hosts=True):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} down'.format(server.fullname))


def bring_up_server(server):
    with fabric.api.settings(host_string=server.deploys_via, disable_known_hosts=True):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))
