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
from veil.environment.in_service import is_server_running

LOGGER = logging.getLogger(__name__)

SSH_KEY_PATH = '/etc/ssh/id_rsa-guard'
KEEP_BACKUP_FOR_DAYS = 5 if VEIL_ENV.is_staging else 10


@script('create-env-backup')
@log_elapsed_time
def create_env_backup():
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['env_backup'] = 'BACKUP'
        return
    hosts_to_backup = [get_veil_host(server.VEIL_ENV.name, server.host_name) for server in unique(list_veil_servers(VEIL_ENV.name,
                                                                                                                    include_guard_server=False,
                                                                                                                    include_monitor_server=False,
                                                                                                                    include_barman_server=False),
                                                                                                  id_func=lambda s: s.host_base_name)]
    if not hosts_to_backup:
        LOGGER.warn('no hosts to backup: %(env_name)s', {'env_name': VEIL_ENV.name})
        return
    with fabric.api.settings(disable_known_hosts=True, key_filename=SSH_KEY_PATH):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        for host in hosts_to_backup:
            backup_host(host)
            fetch_host_backup(host, timestamp)
    shell_execute('rm -f latest && ln -s {} latest'.format(timestamp), cwd=VEIL_BACKUP_ROOT)
    delete_old_backups()
    rsync_to_backup_mirror()


@log_elapsed_time
def backup_host(host):
    host_backup_dir = host.ssh_user_home / 'backup' / host.VEIL_ENV.name / host.base_name
    with fabric.api.settings(host_string='root@{}:{}'.format(host.internal_ip, host.ssh_port)):
        fabric.api.run('mkdir -p -m 0700 {}'.format(host_backup_dir))
        veil_servers = list_veil_servers(VEIL_ENV.name, include_guard_server=False, include_monitor_server=False, include_barman_server=False)
        barman_enabled = any(s.name == 'barman' for s in list_veil_servers(VEIL_ENV.name, include_guard_server=False, include_monitor_server=False))
        if not barman_enabled:
            running_servers_to_down = [s for s in veil_servers
                                       if s.host_base_name == host.base_name and is_server_running(s) and (s.mount_data_dir or is_worker_running_on_server(s))]
        else:
            running_servers_to_down = []
        try:
            if running_servers_to_down:
                bring_down_servers(running_servers_to_down)
            exclude_paths = [host.var_dir.relpathto(host.bucket_inline_static_files_dir),
                             host.var_dir.relpathto(host.bucket_captcha_image_dir),
                             host.var_dir.relpathto(host.bucket_uploaded_files_dir)]
            if barman_enabled:
                exclude_paths.append('data/*-postgresql-*')
            excludes = ' '.join('--exclude "/{}"'.format(path) for path in exclude_paths)
            fabric.api.run('rsync -avh --numeric-ids --delete {excludes} --link-dest={host_var_path}/ {host_var_path}/ {host_backup_dir}/'.format(
                excludes=excludes, host_var_path=host.var_dir, host_backup_dir=host_backup_dir))
        finally:
            if running_servers_to_down:
                bring_up_servers(reversed(running_servers_to_down))


def bring_down_servers(servers):
    for server in servers:
        fabric.api.run('lxc-attach -n {} -- systemctl stop veil-server.service'.format(server.container_name))


def bring_up_servers(servers):
    for server in servers:
        fabric.api.run('lxc-attach -n {} -- systemctl start veil-server.service'.format(server.container_name))


def is_worker_running_on_server(server):
    ret = fabric.api.run("lxc-attach -n {} -- ps -ef | grep 'veil backend job-queue' | grep -v grep".format(server.container_name), warn_only=True)
    return ret.return_code == 0


@log_elapsed_time
def fetch_host_backup(host, timestamp):
    backup_dir = VEIL_BACKUP_ROOT / timestamp
    backup_dir.makedirs(0700)
    host_backup_dir = host.ssh_user_home / 'backup' / host.VEIL_ENV.name / host.base_name
    link_dest = '--link-dest={}/'.format(VEIL_BACKUP_ROOT / 'latest') if (VEIL_BACKUP_ROOT / 'latest').exists() else ''
    server_guard = get_veil_server(VEIL_ENV.name, 'guard')
    if server_guard.host_base_name == host.base_name:
        shell_execute('rsync -avh --numeric-ids --delete {} {} {}/'.format(link_dest, host_backup_dir, backup_dir), debug=True)
    else:
        shell_execute('rsync -avhPz -e "ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no" --numeric-ids --delete {} root@{}:{} {}/'.format(
            SSH_KEY_PATH, host.ssh_port, link_dest, host.internal_ip, host_backup_dir, backup_dir), debug=True)


def delete_old_backups():
    shell_execute('find . -maxdepth 1 -mindepth 1 -type d -ctime +{} -exec rm -r {{}} +'.format(KEEP_BACKUP_FOR_DAYS), cwd=VEIL_BACKUP_ROOT, debug=True)


def rsync_to_backup_mirror():
    backup_mirror = get_current_veil_server().backup_mirror
    if not backup_mirror:
        return
    backup_mirror_path = '~/backup_mirror/{}'.format(VEIL_ENV.name)
    shell_execute('''rsync -avhHPz -e "ssh -i {} -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no" --numeric-ids --delete --bwlimit={} {}/ {}@{}:{}/'''.format(
        SSH_KEY_PATH, backup_mirror.ssh_port, backup_mirror.bandwidth_limit, VEIL_BACKUP_ROOT, backup_mirror.ssh_user, backup_mirror.host_ip,
        backup_mirror_path), debug=True)
