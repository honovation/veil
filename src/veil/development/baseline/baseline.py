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
from veil.backend.database.postgresql_setting import get_pg_data_dir, get_pg_config_dir

BASELINE_DIR = VEIL_HOME / 'baseline' / 'db'


@script('restore-db-from-baseline')
@log_elapsed_time
def restore_db_from_baseline_script(veil_env_name, purpose, remote_download='FALSE'):
    """
    restore db baseline from backup mirror
    barman enabled db baseline path: ~/backup_mirror/<veil_env_name>/latest-database-recover/<purpose>

    Excample:
        veil development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE
        veil development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE TRUE
        veil :ENV_NAME/SERVER_NAME development baseline restore-db-from-baseline ENV_NAME DB_PURPOSE

    @param veil_env_name:
    @param purpose: db purpose
    @param remote_download: 'TRUE' download latest db baseline
    @return:
    """
    if not BASELINE_DIR.exists():
        BASELINE_DIR.makedirs()
    
    if getpwuid(os.stat(BASELINE_DIR).st_uid).pw_name != CURRENT_USER or getgrgid(os.stat(BASELINE_DIR).st_gid).gr_name != CURRENT_USER_GROUP:
        shell_execute('chown {}:{} {}'.format(CURRENT_USER, CURRENT_USER_GROUP, BASELINE_DIR))

    config = postgresql_maintenance_config(purpose)
    if not config:
        print('can not find db: {}'.format(purpose))
        return

    if not any(s.is_barman for s in list_veil_servers(veil_env_name)):
        print('can not restore db as barman is not enabled: {}'.format(purpose))
        return
    local_db_baseline_path = BASELINE_DIR / purpose

    if remote_download == 'TRUE':
        download_baseline(veil_env_name, purpose, local_db_baseline_path)

    print('found postgresql purposes: {}'.format(purpose))

    data_dir = get_pg_data_dir(purpose, config.version)
    config_dir = get_pg_config_dir(purpose, config.version)
    is_local_env = VEIL_ENV.is_dev or VEIL_ENV.is_test
    shell_execute('sudo veil down' if is_local_env else 'sudo systemctl stop veil-server.service', debug=True)
    shell_execute('rsync -avh --delete {}/ {}/'.format(local_db_baseline_path, data_dir), debug=True)
    shell_execute('chmod 700 {}'.format(data_dir))
    shell_execute('ln -sf {}/postgresql.conf .'.format(config_dir), cwd=data_dir)
    shell_execute('ln -sf {}/pg_hba.conf .'.format(config_dir), cwd=data_dir)
    shell_execute('ln -sf {}/pg_ident.conf .'.format(config_dir), cwd=data_dir)
    shell_execute('sudo cp pg_hba.conf pg_hba.conf.ori', cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version))
    shell_execute('printf "local all all trust\nhost all all all trust\n" |sudo tee pg_hba.conf', cwd=config_dir, debug=True)

    config.update(database_client_config(purpose))
    with postgresql_server_running(config.version, data_dir, config.owner):
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
        shell_execute('veil migrate', debug=True)
    shell_execute('veil install-server', debug=True)
    shell_execute('mv pg_hba.conf.ori pg_hba.conf', cwd=config_dir)


@script('download-baseline')
@log_elapsed_time
def download_baseline(veil_env_name, purpose, baseline_path):
    backup_mirror = get_veil_env(veil_env_name).backup_mirror
    if not backup_mirror:
        raise Exception('backup mirror not found in veil env. {}'.format(veil_env_name))

    if isinstance(baseline_path, basestring):
        baseline_path = as_path(baseline_path)
    baseline_path.makedirs(0755)

    backup_mirror_path = VEIL_BACKUP_MIRROR_ROOT / veil_env_name / 'latest-database-recover'
    shell_execute('''rsync -avzhP -e "ssh -p {} -T -x -o Compression=no -o StrictHostKeyChecking=no" --delete --bwlimit={} {}@{}:{}/{}/ {}/'''.format(
        backup_mirror.ssh_port, backup_mirror.bandwidth_limit, backup_mirror.ssh_user, backup_mirror.domain, backup_mirror_path, purpose, baseline_path),
        debug=True)
