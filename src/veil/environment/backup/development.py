from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

BASELINE_DIR = VEIL_HOME / 'baseline'


@script('restore-from-baseline')
def restore_from_baseline(veil_env_name, host_name=None, relative_path=None, force_download=False):
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
    if force_download or not baseline_path.exists():
        download_baseline(veil_env_name, remote_path, baseline_path)
    shell_execute('veil down')
    shell_execute('rsync -avh --delete --link-dest={}/ {}/ {}/'.format(baseline_path, baseline_path, restored_to_path))
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')
    shell_execute('veil down')


@script('download-baseline')
def download_baseline(veil_env_name, remote_path, baseline_path):
    baseline_path.mkdirs()
    server_guard = get_veil_server(veil_env_name, '@guard')
    shell_execute('''rsync -avhPe "ssh -p {} -o StrictHostKeyChecking=no" --delete {}@{}:{}/ {}/'''.format(server_guard.ssh_port,
        server_guard.ssh_user, server_guard.internal_ip, remote_path, baseline_path))
