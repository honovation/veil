from __future__ import unicode_literals, print_function, division
import fabric.api
import fabric.contrib.files
import datetime
import os
import logging
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from veil_component import *

LOGGER = logging.getLogger(__name__)

KEEP_BACKUP_FOR_DAYS = 7 if VEIL_ENV_TYPE == 'staging' else 30

@script('create')
def create_env_backup(should_bring_up_servers='TRUE'):
    """
    Bring down veil servers in sorted server names order
    Bring up veil servers in reversed sorted server names order
    """
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['env_backup'] = 'BACKUP'
        return
    veil_server_names = list_veil_server_names(VEIL_ENV)
    if '@guard' in veil_server_names:
        veil_server_names.remove('@guard')
    for veil_server_name in veil_server_names:
        bring_down_server(VEIL_ENV, veil_server_name)
    try:
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')
        for veil_server_name in veil_server_names:
            backup_server(VEIL_ENV, veil_server_name, timestamp)
        try:
            shell_execute('rm /backup/latest')
        except:
            pass
        shell_execute('ln -s {} latest'.format(timestamp), cwd='/backup')
        delete_old_backups()
    finally:
        if should_bring_up_servers == 'TRUE':
            for veil_server_name in reversed(veil_server_names):
                bring_up_server(VEIL_ENV, veil_server_name)
    rsync_to_backup_mirror()


@script('delete-old-backups')
def delete_old_backups():
    now = datetime.datetime.now()
    for path in as_path('/backup').dirs():
        if 'latest' == path.basename():
            continue
        try:
            backup_time = datetime.datetime.strptime(path.basename(), '%Y%m%d%H%M%S')
            print(now - backup_time)
            if now - backup_time > datetime.timedelta(days=KEEP_BACKUP_FOR_DAYS):
                LOGGER.info('delete old back: %(path)s', {'path': path})
                path.rmtree()
        except:
            LOGGER.exception('failed to parse datetime from %(path)s', {'path': path})


def bring_down_server(backing_up_env, veil_server_name):
    fabric.api.env.host_string = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} down'.format(backing_up_env, veil_server_name))


def bring_up_server(backing_up_env, veil_server_name):
    fabric.api.env.host_string = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} up --daemonize'.format(backing_up_env, veil_server_name))


def backup_server(backing_up_env, veil_server_name, timestamp):
    fabric.api.env.host_string = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    backup_path = '/backup/{}/{}-{}-{}.tar.gz'.format(timestamp, backing_up_env, veil_server_name, timestamp)
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} backup {}'.format(backing_up_env, veil_server_name, backup_path))
    if not os.path.exists('/backup'):
        os.mkdir('/backup', 0755)
    if not os.path.exists('/backup/{}'.format(timestamp)):
        os.mkdir('/backup/{}'.format(timestamp), 0755)
    fabric.api.get(backup_path, backup_path)
    fabric.api.sudo('rm -rf /backup') # backup is centrally stored in @guard lxc container


def rsync_to_backup_mirror():
    current_veil_server = get_current_veil_server()
    if not current_veil_server.backup_mirror_host_string:
        return
    fabric.api.env.host_string = current_veil_server.backup_mirror_host_string
    mirror_host_user = current_veil_server.backup_mirror_host_user
    mirror_host_ip = current_veil_server.backup_mirror_host_ip
    mirror_host_port = current_veil_server.backup_mirror_host_port
    bandwidth_limit = current_veil_server.bandwidth_limit
    backup_mirror_path = '~/backup_mirror/{}'.format(VEIL_ENV)
    if not fabric.contrib.files.exists(backup_mirror_path):
        fabric.api.run('mkdir -p {}'.format(backup_mirror_path))
    shell_execute('''rsync -ave "ssh -p {}" --progress --bwlimit={} --delete /backup/* {}@{}:{}'''.format(
        mirror_host_port, bandwidth_limit, mirror_host_user, mirror_host_ip, backup_mirror_path), shell='sh')