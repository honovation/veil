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
def create_env_backup(should_bring_up_servers='TRUE'):
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
    servers_to_down_before_backup = [server for server in servers if server.mount_data_dir]
    with fabric.api.settings(disable_known_hosts=True, key_filename=SSH_KEY_PATH):
        try:
            for server in servers_to_down_before_backup:
                bring_down_server(server)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            for host in hosts_to_backup:
                backup_host(host, timestamp)
        finally:
            if should_bring_up_servers == 'TRUE':
                for server in reversed(servers_to_down_before_backup):
                    bring_up_server(server)
        for host in hosts_to_backup:
            fetch_host_backup(host, timestamp)
        shell_execute('ln -sf {} latest'.format(timestamp), cwd=BACKUP_ROOT)
        delete_old_backups()
        rsync_to_backup_mirror()


@script('delete-old-backups')
def delete_old_backups():
    shell_execute('find . -type d -ctime +{} -exec rm -r {} +'.format(KEEP_BACKUP_FOR_DAYS), cwd=BACKUP_ROOT)


def bring_down_server(server):
    with fabric.api.settings(host_string=server.deploys_via):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} down'.format(server.fullname))


def bring_up_server(server):
    with fabric.api.settings(host_string=server.deploys_via):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))


def backup_host(host, timestamp):
    host_backup_dir = host.ssh_user_home / 'tmp' / BACKUP_ROOT[1:] / timestamp
    backup_file_template = '{}_{}_{{}}_{}.tar.gz'.format(host.env_name, host.base_name, timestamp)
    with fabric.api.settings(host_string=host.deploys_via):
        with fabric.api.cd(host.veil_home):
            fabric.api.run('veil :{} backup {} {} {}'.format(host.env_name, host.base_name, host_backup_dir, backup_file_template))


def fetch_host_backup(host, timestamp):
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.makedirs(0755)
    host_backup_dir = host.ssh_user_home / 'tmp' / BACKUP_ROOT[1:] / timestamp
    with fabric.api.settings(host_string=host.deploys_via):
        fabric.api.get(host_backup_dir / '*', backup_dir)
        fabric.api.run('rm -rf {}/*'.format(host_backup_dir.parent))


def rsync_to_backup_mirror():
    backup_mirror = get_current_veil_server().backup_mirror
    if not backup_mirror:
        return
    backup_mirror_path = '~/backup_mirror/{}/'.format(VEIL_ENV_NAME)
    shell_execute('''rsync -avPe "ssh -i {} -p {} -o StrictHostKeyChecking=no" --bwlimit={} --delete {}/ {}@{}:{}'''.format(SSH_KEY_PATH,
        backup_mirror.ssh_port, backup_mirror.bandwidth_limit, BACKUP_ROOT, backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror_path))
