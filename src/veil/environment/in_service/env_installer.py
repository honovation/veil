from __future__ import unicode_literals, print_function, division
from datetime import datetime
import sys
import fabric.api
import fabric.contrib.files
from veil.development.git import *
from veil.utility.misc import *
from veil.utility.timer import *
from veil_component import *
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.clock import *
from veil.utility.shell import *
from veil.backend.database.migration import *
from .host_installer import veil_hosts_resource, veil_hosts_application_codebase_resource
from .server_installer import veil_servers_resource


def display_deployment_memo(veil_env_name):
    deployment_memo = get_veil_env_deployment_memo(veil_env_name)
    if deployment_memo:
        print('!!! IMPORTANT !!!')
        print(deployment_memo)
        print('type "i will do it" without space to continue:')
        while True:
            if 'iwilldoit' == sys.stdin.readline().strip():
                break


def are_all_servers_ever_deployed(servers):
    for server in servers:
        with fabric.api.settings(host_string=server.deploys_via):
            if not fabric.contrib.files.exists(server.deployed_tag_path):
                return False
    return True


@script('deploy-env')
@log_elapsed_time
def deploy_env(veil_env_name, config_dir, should_download_packages='TRUE'):
    """
    Bring down veil servers in sorted server names order (in create-backup)
    Bring up veil servers in reversed sorted server names order (in veil_servers_resource and local_deployer:deploy)

    should_download_packages: set to FALSE when download-packages before deploy-env
    """
    do_local_preparation(veil_env_name)
    tag_deploy(veil_env_name)
    servers = list_veil_servers(veil_env_name)
    ever_deployed = are_all_servers_ever_deployed(servers)
    if ever_deployed:
        make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True)
    install_resource(veil_hosts_resource(veil_env_name=veil_env_name, config_dir=as_path(config_dir)))
    if ever_deployed:
        if 'TRUE' == should_download_packages:
            download_packages(veil_env_name)
        stop_env(veil_env_name)
        make_rollback_backup(veil_env_name, exclude_code_dir=True, exclude_data_dir=False)
    install_resource(veil_servers_resource(servers=servers[::-1], action='DEPLOY'))


def make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        source_dir = host.env_dir
        backup_dir = '{}-backup'.format(source_dir)
        excludes = []
        if exclude_code_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.code_dir)))
        if exclude_data_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.data_dir)))
        with fabric.api.settings(host_string=host.deploys_via):
            fabric.api.sudo('rsync -a --delete {} {}/ {}/'.format(' '.join(excludes), source_dir, backup_dir))


@script('download-packages')
def download_packages(veil_env_name):
    # this command should not interrupt normal website operation
    # designed to run when website is still running, to prepare for a full deployment
    hosts = list_veil_hosts(veil_env_name)
    hosts_retrieved_latest_version = []
    for host in hosts:
        with fabric.api.settings(host_string=host.deploys_via):
            with fabric.api.cd(host.veil_home):
                if host.base_name not in hosts_retrieved_latest_version:
                    with fabric.api.settings(forward_agent=True):
                        fabric.api.sudo('git archive --format=tar --remote=origin master RESOURCE-LATEST-VERSION-* | tar -x')
                    hosts_retrieved_latest_version.append(host.base_name)
                try:
                    for server in host.server_list:
                        with fabric.api.settings(host_string=server.deploys_via):
                            with fabric.api.cd(server.veil_home):
                                fabric.api.sudo('veil :{} install-server --download-only'.format(server.fullname))
                finally:
                    fabric.api.sudo('git checkout -- RESOURCE-LATEST-VERSION-*')


@script('patch-env')
@log_elapsed_time
def patch_env(veil_env_name):
    """
    Iterate veil server in reversed sorted server names order (in veil_servers_resource and local_deployer:patch)
        and patch programs
    """
    do_local_preparation(veil_env_name)
    tag_patch(veil_env_name)
    install_resource(veil_hosts_application_codebase_resource(veil_env_name=veil_env_name))
    install_resource(veil_servers_resource(servers=list_veil_servers(veil_env_name)[::-1], action='PATCH'))


def do_local_preparation(veil_env_name):
    check_no_changes_not_committed()
    check_no_commits_not_pushed()
    check_no_migration_scripts_not_locked()
    check_no_locked_migration_scripts_changed()
    display_deployment_memo(veil_env_name)
    update_branch(veil_env_name)


@script('rollback-env')
def rollback_env(veil_env_name):
    """
    Bring down veil servers in sorted server names order (in rollback)
    Bring up veil servers in reversed sorted server names order
    """
    hosts = unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name)
    check_rollback_backup(hosts)
    stop_env(veil_env_name)
    rollback(hosts)
    start_env(veil_env_name)


def check_rollback_backup(hosts):
    for host in hosts:
        backup_dir = '{}-backup'.format(host.env_dir)
        with fabric.api.settings(host_string=host.deploys_via):
            if not fabric.contrib.files.exists(backup_dir):
                raise Exception('{}: backup does not exist'.format(host.base_name))


def rollback(hosts):
    ensure_servers_down(hosts)
    for host in hosts:
        source_dir = host.env_dir
        backup_dir = '{}-backup'.format(source_dir)
        with fabric.api.settings(host_string=host.deploys_via):
            if fabric.contrib.files.exists(source_dir):
                left_over_dir = '{}-to-be-deleted-{}'.format(source_dir, datetime.now().strftime('%Y%m%d%H%M%S'))
                fabric.api.sudo('rsync -a --delete --link-dest={}/ {}/ {}/'.format(backup_dir, source_dir, left_over_dir))
            fabric.api.sudo('rsync -a --delete {}/ {}/'.format(backup_dir, source_dir))


def ensure_servers_down(hosts):
    for host in hosts:
        try:
            with fabric.api.settings(host_string=host.deploys_via):
                fabric.api.sudo('ps -ef | grep supervisord | grep {} | grep -v grep'.format(host.etc_dir))
        except:
            pass
        else:
            raise Exception('{}: can not rollback while not all veil servers are down'.format(host.base_name))


@script('backup-env')
def backup_env(veil_env_name):
    server_guard = get_veil_server(veil_env_name, '@guard')
    with fabric.api.settings(host_string=server_guard.deploys_via):
        with fabric.api.cd(server_guard.veil_home):
            fabric.api.sudo('veil :{} backup-env'.format(server_guard.fullname))


@script('purge-left-overs')
def purge_left_overs(veil_env_name):
    hosts = unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name)
    for host in hosts:
        with fabric.api.settings(host_string=host.deploys_via):
            fabric.api.sudo('rm -rf {}-to-be-deleted-*'.format(host.env_dir))


@script('restart-env')
def restart_env(veil_env_name):
    """
    Bring down veil servers in sorted server names order
    Bring up veil servers in reversed sorted server names order
    """
    stop_env(veil_env_name)
    start_env(veil_env_name)


@script('stop-env')
def stop_env(veil_env_name):
    """
    Bring down veil servers in sorted server names order
    """
    for server in list_veil_servers(veil_env_name):
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} down'.format(server.fullname))


@script('start-env')
def start_env(veil_env_name):
    """
    Bring up veil servers in reversed sorted server names order
    """
    for server in reversed(list_veil_servers(veil_env_name)):
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))


@script('upgrade-env-pip')
def upgrade_env_pip(veil_env_name, setuptools_version, pip_version):
    """
    Upgrade pip and setuptools on veil servers
    """
    for server in list_veil_servers(veil_env_name):
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} upgrade-pip {} {}'.format(server.fullname, setuptools_version, pip_version))


@script('print-deployed-at')
def print_deployed_at():
    print(get_deployed_at())


def get_deployed_at():
    last_commit = shell_execute('git rev-parse HEAD', capture=True)
    lines = shell_execute("git show-ref --tags -d | grep ^{} | sed -e 's,.* refs/tags/,,' -e 's/\^{{}}//'".format(last_commit), capture=True)
    deployed_ats = []
    for tag in lines.splitlines(False):
        if tag.startswith('{}-'.format(VEIL_ENV_NAME)):
            formatted_deployed_at = tag.replace('{}-'.format(VEIL_ENV_NAME), '').split('-')[0]
            deployed_ats.append(convert_datetime_to_client_timezone(datetime.strptime(formatted_deployed_at, '%Y%m%d%H%M%S')))
    return max(deployed_ats) if deployed_ats else None


def update_branch(veil_env_name):
    print('update env-{} branch...'.format(veil_env_name))
    try:
        shell_execute('git checkout -B env-{}'.format(veil_env_name), cwd=VEIL_HOME)
        shell_execute('git merge master --ff-only', cwd=VEIL_HOME)
        shell_execute('git push origin env-{}'.format(veil_env_name), cwd=VEIL_HOME)
    finally:
        shell_execute('git checkout master', cwd=VEIL_HOME)


def tag_deploy(veil_env_name):
    tag_name = '{}-{}-{}'.format(
        veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))


def tag_patch(veil_env_name):
    tag_name = '{}-{}-{}-patch'.format(
        veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))
