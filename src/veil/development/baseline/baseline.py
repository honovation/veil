from __future__ import unicode_literals, print_function, division

from time import sleep
import os
from pwd import getpwuid
from grp import getgrgid
from veil_component import as_path
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *
from veil.backend.database.client import *
from veil.backend.database.postgresql import *

BASELINE_DIR = VEIL_HOME / 'baseline'


@script('restore-db-from-baseline')
@log_elapsed_time
def restore_db_from_baseline_script(veil_env_name, purpose, remote_download='FALSE'):
    """
    restore db baseline from backup mirror
    barman enabled db baseline path: backup_mirror/<veil_env_name>/<purpose>-db
    non barman enabled db baseline path: backup_mirror/<veil_env_name>/latest/<host_name>/data/<purpose>-postgresql-<version>

    Excample:
        veil development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE
        veil development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE TRUE
        sudo -E veil :ENV_NAME/SERVER_NAME development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE

    @param veil_env_name:
    @param purpose: db purpose
    @param remote_download: 'TRUE' download latest db baseline
    @return:
    """
    if not BASELINE_DIR.exists():
        BASELINE_DIR.mkdir()
    
    if getpwuid(os.stat(BASELINE_DIR).st_uid).pw_name != CURRENT_USER or getgrgid(os.stat(BASELINE_DIR).st_gid).gr_name != CURRENT_USER_GROUP:
        shell_execute('chown {}:{} {}'.format(CURRENT_USER, CURRENT_USER_GROUP, BASELINE_DIR))

    config = postgresql_maintenance_config(purpose)
    if not config:
        print('can not find db: {}'.format(purpose))
        return

    db_path_name = '{}-postgresql-{}'.format(purpose, config.version)
    barman_enabled = any(s.name == 'barman' for s in list_veil_servers(veil_env_name))
    if barman_enabled:
        remote_db_baseline_path = '{}-db'.format(purpose)
        local_db_baseline_path = BASELINE_DIR / remote_db_baseline_path
    else:
        host_name = None
        for server in list_veil_servers(veil_env_name):
            if server.mount_data_dir:
                host_name = server.host_name
                break
        if not host_name:
            print('can not find mounted data host name for env: {}'.format(veil_env_name))
            return
        host = get_veil_host(veil_env_name, host_name)
        remote_db_baseline_path = 'latest/{}/data/{}'.format(host.base_name, db_path_name)
        local_db_baseline_path = BASELINE_DIR / veil_env_name / host.base_name / 'data' / db_path_name

    if remote_download == 'TRUE':
        download_baseline(veil_env_name, remote_db_baseline_path, local_db_baseline_path)

    print('found postgresql purposes: {}'.format(purpose))
    restored_to_path = VEIL_DATA_DIR / db_path_name
    is_local_env = VEIL_ENV.is_dev or VEIL_ENV.is_test
    shell_execute('sudo veil down' if is_local_env else 'sudo systemctl stop veil-server.service', debug=True)
    shell_execute('rsync -avh --delete {}/ {}/'.format(local_db_baseline_path, restored_to_path), debug=True)
    shell_execute('veil install-server', debug=True)

    db_config_path = VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version)
    shell_execute('sudo cp pg_hba.conf pg_hba.conf.ori', cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version))
    shell_execute('printf "local all all trust\nhost all all all trust\n" |sudo tee pg_hba.conf', cwd=db_config_path, debug=True)

    shell_execute('sudo veil up --daemonize' if is_local_env else 'sudo systemctl start veil-server.service', debug=True)

    config.update(database_client_config(purpose))
    while True:
        # set db owner password and run in a loop to wait PG to start
        try:
            shell_execute(
                '''psql -p {} -d template1 -U {} -c "ALTER ROLE {} WITH PASSWORD '{}'"'''.format(config.port, config.owner, config.owner,
                                                                                                 config.owner_password))
            # set db user password
            shell_execute(
                '''psql -p {} -d template1 -U {} -c "ALTER ROLE {} WITH PASSWORD '{}'"'''.format(config.port, config.user, config.user, config.password))
        except Exception:
            print('retrying')
            sleep(2)
        else:
            break
    shell_execute('mv pg_hba.conf.ori pg_hba.conf', cwd=db_config_path)

    shell_execute('veil migrate', debug=True)

    shell_execute('sudo veil down' if is_local_env else 'sudo systemctl stop veil-server.service', debug=True)


@script('restore-from-baseline')
@log_elapsed_time
def restore_from_baseline(veil_env_name, force_download='FALSE', relative_path=None, host_name=None):
    if not host_name:
        for server in list_veil_servers(veil_env_name):
            if server.mount_data_dir:
                host_name = server.host_name
                break
    host = get_veil_host(veil_env_name, host_name)
    if not relative_path:
        assert any(server.mount_data_dir for server in host.server_list), 'Please specify relative_path'
        relative_path = host.var_dir.relpathto(host.data_dir)
    if relative_path == '*':
        remote_path = as_path('latest') / host.base_name
        baseline_path = BASELINE_DIR / veil_env_name / host.base_name
        restored_to_path = VEIL_VAR_DIR
    else:
        remote_path = as_path('latest') / host.base_name / relative_path
        baseline_path = BASELINE_DIR / veil_env_name / host.base_name / relative_path
        restored_to_path = VEIL_VAR_DIR / relative_path
    if force_download.upper() == 'TRUE' or not baseline_path.exists():
        download_baseline(veil_env_name, remote_path, baseline_path)

    shell_execute('veil down', debug=True)
    shell_execute('rsync -avh --delete {}/ {}/'.format(baseline_path, restored_to_path), debug=True)
    shell_execute('veil install-server', debug=True)


@script('download-baseline')
@log_elapsed_time
def download_baseline(veil_env_name, remote_path, baseline_path):
    if isinstance(baseline_path, basestring):
        baseline_path = as_path(baseline_path)
    baseline_path.makedirs(0755)
    backup_mirror = None
    for server in get_veil_env(veil_env_name).servers:
        if server.is_guard_server:
            backup_mirror = get_veil_server(veil_env_name, server.name).backup_mirror
            if backup_mirror:
                break
    if not backup_mirror:
        raise Exception('backup mirror not found on server {}/guard'.format(veil_env_name))
    if not hasattr(backup_mirror, 'domain'):
        backup_mirror.domain = get_backup_mirror_domain()
    backup_mirror_path = '~/backup_mirror/{}'.format(veil_env_name)
    shell_execute('''rsync -avhPz -e "ssh -p {} -T -x -o Compression=yes -o StrictHostKeyChecking=no" --delete --bwlimit={} {}@{}:{}/{}/ {}/'''.format(
        backup_mirror.ssh_port, backup_mirror.bandwidth_limit, backup_mirror.ssh_user, backup_mirror.domain, backup_mirror_path, remote_path,
        baseline_path), debug=True)
