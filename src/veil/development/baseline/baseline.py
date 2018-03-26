from __future__ import unicode_literals, print_function, division

from time import sleep

from veil_component import as_path
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *
from veil.backend.database.client import *
from veil.backend.database.postgresql import *

BASELINE_DIR = VEIL_HOME / 'baseline'


@script('restore-from-baseline')
@log_elapsed_time
def restore_from_baseline(veil_env_name, force_download='FALSE', relative_path=None, host_name=None):
    """
    Examples:
        sudo -E veil :xxx-staging/db restore-from-baseline xxx-public TRUE data/xxx-postgresql-9.4
        sudo -E veil restore-from-baseline xxx-public TRUE data/xxx-postgresql-9.4
        sudo -E veil restore-from-baseline xxx-public FALSE data/xxx-postgresql-9.4
    """
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

    purposes = []
    if VEIL_DATA_DIR.startswith(restored_to_path):
        for pg_data_dir in VEIL_DATA_DIR.dirs('*-postgresql-*'):
            purposes.append(pg_data_dir.name.split('-postgresql-', 1)[0])
    elif restored_to_path.startswith(VEIL_DATA_DIR) and '-postgresql-' in restored_to_path.name:
        purposes.append(restored_to_path.name.split('-postgresql-', 1)[0])
    print('found postgresql purposes: {}'.format(purposes))
    for purpose in purposes:
        # set db conf permission
        config = postgresql_maintenance_config(purpose)
        shell_execute('cp pg_hba.conf pg_hba.conf.ori', cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version))
        shell_execute('printf "local all all trust\nhost all all 127.0.0.1/32 trust" > pg_hba.conf', cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version))
        shell_execute('chown -f {}:{} *'.format(CURRENT_USER, CURRENT_USER_GROUP),
                      cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version), debug=True)

    shell_execute('veil up --daemonize', debug=True)
    for purpose in purposes:
        config = postgresql_maintenance_config(purpose)
        config.update(database_client_config(purpose))
        while True:
            # set db owner password and run in a loop to wait PG to start
            try:
                shell_execute(
                    '''psql -p {} -d template1 -U {} -c "ALTER ROLE {} WITH PASSWORD '{}'"'''.format(config.port, config.owner, config.owner, config.owner_password))
                # set db user password
                shell_execute(
                    '''psql -p {} -d template1 -U {} -c "ALTER ROLE {} WITH PASSWORD '{}'"'''.format(config.port, config.user, config.user, config.password))
            except Exception:
                print('retrying')
                sleep(2)
            else:
                break
        shell_execute('mv pg_hba.conf.ori pg_hba.conf', cwd=VEIL_ETC_DIR / '{}-postgresql-{}'.format(purpose, config.version))
    shell_execute('veil migrate', debug=True)

    shell_execute('veil down', debug=True)


@script('download-baseline')
@log_elapsed_time
def download_baseline(veil_env_name, remote_path, baseline_path):
    if isinstance(baseline_path, basestring):
        baseline_path = as_path(baseline_path)
    baseline_path.makedirs(0755)
    backup_mirror = get_veil_server(veil_env_name, 'guard').backup_mirror
    if not backup_mirror:
        raise Exception('backup mirror not found on server {}/{}'.format(veil_env_name, 'guard'))
    if not hasattr(backup_mirror, 'domain'):
        backup_mirror.domain = 'ljhost-01.dmright.com'
    backup_mirror_path = '~/backup_mirror/{}'.format(veil_env_name)
    shell_execute('''rsync -avhPz -e "ssh -p {} -T -x -o Compression=yes -o StrictHostKeyChecking=no" --delete --bwlimit={} {}@{}:{}/{}/ {}/'''.format(
        backup_mirror.ssh_port, backup_mirror.bandwidth_limit, backup_mirror.ssh_user, backup_mirror.domain, backup_mirror_path, remote_path,
        baseline_path), debug=True)
