from __future__ import unicode_literals, print_function, division
import fabric.api
from datetime import datetime, timedelta
import logging
from veil_component import as_path
from veil.environment import *
from veil_installer import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.misc import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

SSH_KEY_PATH = '/etc/ssh/id_rsa-@guard'
KEEP_BACKUP_FOR_DAYS = 3 if VEIL_ENV_TYPE == 'staging' else 15


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
    with fabric.api.settings(disable_known_hosts=True, key_filename=SSH_KEY_PATH):
        try:
            for server in servers:
                bring_down_server(server)
            now = datetime.now()
            timestamp = now.strftime('%Y%m%d%H%M%S')
            backup_dir = as_path('/backup/{}'.format(timestamp))
            backup_dir.makedirs(0755)
            for host in [get_veil_host(server.env_name, server.host_name) for server in unique(servers, id_func=lambda s: s.host_base_name)]:
                backup_file_template = '{}_{}_{{}}_{}.tar.gz'.format(host.env_name, host.base_name, timestamp)
                backup_host(host, backup_dir, backup_file_template)
            shell_execute('ln -snf {} latest'.format(timestamp), cwd=backup_dir.parent)
        finally:
            if should_bring_up_servers == 'TRUE':
                for server in reversed(servers):
                    bring_up_server(server)
        delete_old_backups()
        rsync_to_backup_mirror()


@script('delete-old-backups')
def delete_old_backups():
    now = datetime.now()
    for path in as_path('/backup').dirs():
        if 'latest' == path.basename():
            continue
        try:
            backup_time = datetime.strptime(path.basename(), '%Y%m%d%H%M%S')
            if now - backup_time > timedelta(days=KEEP_BACKUP_FOR_DAYS):
                LOGGER.info('delete old back: %(path)s', {'path': path})
                path.rmtree()
        except:
            LOGGER.exception('failed to parse datetime from %(path)s', {'path': path})


def bring_down_server(server):
    with fabric.api.settings(host_string=server.deploys_via):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} down'.format(server.fullname))


def bring_up_server(server):
    with fabric.api.settings(host_string=server.deploys_via):
        with fabric.api.cd(server.veil_home):
            fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))


def backup_host(host, backup_dir, backup_file_template):
    host_backup_dir = host.ssh_user_home / 'tmp' / backup_dir[1:]
    with fabric.api.settings(host_string=host.deploys_via):
        with fabric.api.cd(host.veil_home):
            fabric.api.run('veil :{} backup {} {}'.format(host.env_name, host_backup_dir, backup_file_template))
        fabric.api.get(host_backup_dir / '*', backup_dir)
        fabric.api.run('rm -rf {}'.format(host_backup_dir))  # backup is centrally stored in @guard container


def rsync_to_backup_mirror():
    backup_mirror = get_current_veil_server().backup_mirror
    if not backup_mirror:
        return
    backup_mirror_path = '~/backup_mirror/{}/'.format(VEIL_ENV_NAME)
    with fabric.api.settings(host_string=backup_mirror.deploys_via):
        fabric.api.run('mkdir -p {}'.format(backup_mirror_path))
    shell_execute('''rsync -ave "ssh -i {} -p {} -o StrictHostKeyChecking=no" --progress --bwlimit={} --delete /backup/ {}@{}:{}'''.format(
        SSH_KEY_PATH, backup_mirror.ssh_port, backup_mirror.bandwidth_limit, backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror_path))
