from __future__ import unicode_literals, print_function, division
from veil_component import as_path
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *

BASELINE_DIR = VEIL_HOME / 'baseline'


@script('restore-from-baseline')
@log_elapsed_time
def restore_from_baseline(veil_env_name, force_download='FALSE', relative_path=None, host_name=None):
    """
    Examples:
        sudo veil restore-from-baseline ljmall-public TRUE data/ljmall-postgresql-9.3
        sudo veil restore-from-baseline ljmall-public FALSE data/ljmall-postgresql-9.3
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
        remote_path = VEIL_BACKUP_ROOT / 'latest' / host.base_name
        baseline_path = BASELINE_DIR / veil_env_name / host.base_name
        restored_to_path = VEIL_VAR_DIR
    else:
        remote_path = VEIL_BACKUP_ROOT / 'latest' / host.base_name / relative_path
        baseline_path = BASELINE_DIR / veil_env_name / host.base_name / relative_path
        restored_to_path = VEIL_VAR_DIR / relative_path
    if force_download.upper() == 'TRUE' or not baseline_path.exists():
        download_baseline(veil_env_name, remote_path, baseline_path)
    shell_execute('veil down')
    shell_execute('rsync -avh --delete --link-dest={}/ {}/ {}/'.format(baseline_path, baseline_path, restored_to_path), debug=True)
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    if VEIL_ENV_TYPE == 'development':
        password = 'p@55word'
    elif VEIL_ENV_TYPE == 'staging':
        password = 'p@55wordStag'
    else:
        raise Exception('Invalid env type')
    shell_execute('''sudo -u dejavu psql -d template1 -c "ALTER ROLE dejavu WITH PASSWORD '{}'"'''.format(password))
    shell_execute('''sudo -u dejavu psql -d template1 -c "ALTER ROLE veil WITH PASSWORD '{}'"'''.format(password))
    shell_execute('veil migrate')
    shell_execute('veil down')


@script('download-baseline')
@log_elapsed_time
def download_baseline(veil_env_name, remote_path, baseline_path):
    #TODO: download from BACKUP MIRROR
    if isinstance(baseline_path, basestring):
        baseline_path = as_path(baseline_path)
    baseline_path.makedirs(0755)
    guard_key = as_path('../ljsecurity') / veil_env_name / '.ssh-@guard' / 'id_rsa'
    server_guard = get_veil_server(veil_env_name, '@guard')
    host_guard = get_veil_host(veil_env_name, server_guard.host_name)
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server_guard.container_name)
    shell_execute('''rsync -avhPz -e "ssh -i {} -p {} -T -x -c arcfour -o Compression=no -o StrictHostKeyChecking=no" --delete root@{}:{}/{}/ {}/'''.format(
        guard_key, host_guard.ssh_port, host_guard.internal_ip, container_rootfs_path, remote_path, baseline_path), debug=True)
