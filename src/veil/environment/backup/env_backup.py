from __future__ import unicode_literals, print_function, division
import fabric.api
from datetime import datetime
import logging
from veil.environment import *
from veil_installer import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.misc import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

SSH_KEY_PATH = '/etc/ssh/id_rsa-@guard'
KEEP_BACKUP_FOR_DAYS = 3 if VEIL_ENV_TYPE == 'staging' else 10


@script('create-env-backup')
@log_elapsed_time
def create_env_backup():
    """
    Bring down veil servers in sorted server names order
    Bring up veil servers in reversed sorted server names order
    """
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['env_backup'] = 'BACKUP'
        return
    servers = [server for server in list_veil_servers(VEIL_ENV_NAME) if server.name not in ('@guard', '@monitor')]
    hosts_to_backup = [get_veil_host(server.env_name, server.host_name) for server in unique(servers, id_func=lambda s: s.host_base_name)]
    with fabric.api.settings(disable_known_hosts=True, key_filename=SSH_KEY_PATH):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        for host in hosts_to_backup:
            with fabric.api.settings(host_string=host.deploys_via):
                backup_host(host, timestamp)
                fetch_host_backup(host, timestamp)
    shell_execute('ln -sf {} latest'.format(timestamp), cwd=VEIL_BACKUP_ROOT)
    delete_old_backups()
    rsync_to_backup_mirror()


def backup_host(host, timestamp):
    host_backup_dir = host.ssh_user_home / 'tmp' / VEIL_BACKUP_ROOT[1:] / timestamp
    backup_file_template = '{}_{}_{{}}_{}.tar.gz'.format(host.env_name, host.base_name, timestamp)
    fabric.api.run('mkdir -p {}'.format(host_backup_dir))
    with fabric.api.cd(VEIL_VAR_DIR):
        servers_to_down = [s for s in list_veil_servers(VEIL_ENV_NAME) if s.mount_data_dir and s.host_base_name == host.base_name and is_server_running(s)]
        for subdir_name in fabric.api.run('find . -maxdepth 1 -mindepth 1 -type d -printf "%P\n"', warn_only=True).splitlines():
            subdir_backup_path = host_backup_dir / backup_file_template.format(subdir_name)
            backup_host_dir(subdir_name, subdir_backup_path, servers_to_down)


def is_server_running(server):
    ret = fabric.api.run('ps -ef | grep supervisord | grep -e {}/{} | grep -v grep'.format(VEIL_ETC_DIR.parent, server.name), warn_only=True)
    return ret.return_code == 0


@log_elapsed_time
def backup_host_dir(dir_name, backup_path, servers_to_down):
    try:
        if VEIL_DATA_DIR.name == dir_name:
            bring_down_servers(servers_to_down)
        fabric.api.run('tar -cpzf {} {} --exclude=uploaded-files --exclude=inline-static-files --exclude=captcha-image'.format(backup_path, dir_name))
    finally:
        if VEIL_DATA_DIR.name == dir_name:
            bring_up_servers(reversed(servers_to_down))


def bring_down_servers(servers):
    for server in servers:
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} down'.format(server.fullname))


def bring_up_servers(servers):
    for server in servers:
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))


def fetch_host_backup(host, timestamp):
    host_backup_dir = host.ssh_user_home / 'tmp' / VEIL_BACKUP_ROOT[1:] / timestamp
    server_guard = get_veil_server(VEIL_ENV_NAME, '@guard')
    if server_guard.host_base_name == host.base_name:
        VEIL_BACKUP_ROOT.makedirs(0755)
        shell_execute('mv {} {}'.format(host_backup_dir, VEIL_BACKUP_ROOT))
        shell_execute('rm -rf {}/*'.format(host_backup_dir.parent))
    else:
        backup_dir = VEIL_BACKUP_ROOT / timestamp
        backup_dir.makedirs(0755)
        fabric.api.get(host_backup_dir / '*', backup_dir)
        fabric.api.run('rm -rf {}/*'.format(host_backup_dir.parent))


def delete_old_backups():
    shell_execute('find . -type d -ctime +{} -exec rm -r {{}} +'.format(KEEP_BACKUP_FOR_DAYS), cwd=VEIL_BACKUP_ROOT)


def rsync_to_backup_mirror():
    backup_mirror = get_current_veil_server().backup_mirror
    if not backup_mirror:
        return
    backup_mirror_path = '~/backup_mirror/{}/'.format(VEIL_ENV_NAME)
    shell_execute('''rsync -avPe "ssh -i {} -p {} -o StrictHostKeyChecking=no" --bwlimit={} --delete {}/ {}@{}:{}'''.format(SSH_KEY_PATH,
        backup_mirror.ssh_port, backup_mirror.bandwidth_limit, VEIL_BACKUP_ROOT, backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror_path))
