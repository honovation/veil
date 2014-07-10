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
from .host_installer import veil_hosts_resource, veil_hosts_codebase_resource
from .server_installer import veil_servers_resource, is_container_running, is_server_running


@script('deploy-env')
@log_elapsed_time
def deploy_env(veil_env_name, config_dir, should_download_packages='TRUE', include_monitor_server='FALSE'):
    print(green('Make local preparation ...'))
    do_local_preparation(veil_env_name)
    print(green('Tag deploy ...'))
    tag_deploy(veil_env_name)

    print(green('Make rollback backup -- include code dir, exclude data dir ...'))
    make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True)
    print(green('Deploy hosts ...'))
    install_resource(veil_hosts_resource(veil_env_name=veil_env_name, config_dir=as_path(config_dir)))
    if should_download_packages == 'TRUE':
        print(green('Download packages ...'))
        download_packages(veil_env_name)
    first_round_servers = list_veil_servers(veil_env_name, False, False)
    first_round_server_names = [server.name for server in first_round_servers]
    print(green('Stop round-1 servers {} ...'.format(first_round_server_names)))
    stop_servers(first_round_servers)
    print(green('Make rollback backup -- exclude code dir, include data dir ...'))
    make_rollback_backup(veil_env_name, exclude_code_dir=True, exclude_data_dir=False)
    print(green('Deploy round-1 servers {} ...'.format(first_round_server_names[::-1])))
    install_resource(veil_servers_resource(servers=first_round_servers[::-1], action='DEPLOY'))

    second_round_servers = [get_veil_server(veil_env_name, '@guard')]
    second_round_server_names = [server.name for server in second_round_servers]
    if include_monitor_server == 'TRUE':
        second_round_servers.append(get_veil_server(veil_env_name, '@monitor'))
    print(green('Stop round-2 servers {} ...'.format(second_round_server_names)))
    stop_servers(second_round_servers)
    print(green('Deploy round-2 servers {} ...'.format(second_round_server_names[::-1])))
    install_resource(veil_servers_resource(servers=second_round_servers[::-1], action='DEPLOY'))

    print(green('Remove rollbackable tags ...'))
    remove_rollbackable_tags(veil_env_name)


def make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        source_dir = host.env_dir
        rollback_backup_dir = '{}-backup'.format(source_dir)
        excludes = []
        if exclude_code_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.code_dir)))
        if exclude_data_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.data_dir)))
        with fabric.api.settings(host_string=host.deploys_via):
            if not fabric.contrib.files.exists(source_dir):
                continue
            fabric.api.sudo('rsync -ah --numeric-ids --delete {} --link-dest={}/ {}/ {}/'.format(' '.join(excludes), source_dir, source_dir,
                rollback_backup_dir))
            fabric.api.sudo('touch {}'.format(host.rollbackable_tag_path))


def remove_rollbackable_tags(veil_env_name):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        with fabric.api.settings(host_string=host.deploys_via):
            fabric.api.sudo('rm -f {}'.format(host.rollbackable_tag_path))


@script('download-packages')
def download_packages(veil_env_name):
    # this command should not interrupt normal website operation
    # designed to run when website is still running, to prepare for a full deployment
    for host in list_veil_hosts(veil_env_name):
        with fabric.api.settings(host_string=host.deploys_via):
            with fabric.api.cd(host.veil_home):
                with fabric.api.settings(forward_agent=True):
                    fabric.api.sudo('git archive --format=tar --remote=origin master RESOURCE-LATEST-VERSION-* | tar -x')
                try:
                    for server in host.server_list:
                        print(green('Download packages for server {} ...'.format(server.name)))
                        if not fabric.contrib.files.exists(server.deployed_tag_path):
                            print(yellow('Skipped downloading packages for server {} as it is not successfully deployed'.format(
                                server.container_name)))
                            continue
                        if not is_container_running(server):
                            print(yellow('Skipped downloading packages for server {} as its container is not running'.format(server.container_name)))
                            continue
                        with fabric.api.settings(host_string=server.deploys_via):
                            with fabric.api.cd(server.veil_home):
                                fabric.api.sudo('veil :{} install-server --download-only'.format(server.fullname))
                finally:
                    fabric.api.sudo('git checkout -- RESOURCE-LATEST-VERSION-*')


@script('deploy-monitor')
@log_elapsed_time
def deploy_monitor(veil_env_name):
    server = get_veil_server(veil_env_name, '@monitor')
    stop_servers([server])
    install_resource(veil_servers_resource(servers=[server], action='DEPLOY'))


@script('patch-env')
@log_elapsed_time
def patch_env(veil_env_name):
    """
    Iterate veil server in reversed sorted server names order (in veil_servers_resource and local_deployer:patch)
        and patch programs
    """
    print(green('Make local preparation ...'))
    do_local_preparation(veil_env_name)
    print(green('Tag patch ...'))
    tag_patch(veil_env_name)
    print(green('Pull codebase ...'))
    install_resource(veil_hosts_codebase_resource(veil_env_name=veil_env_name))
    servers = list_veil_servers(veil_env_name, False, False)
    server_names = [server.name for server in servers]
    print(green('Patch servers {} ...'.format(server_names[::-1])))
    install_resource(veil_servers_resource(servers=servers[::-1], action='PATCH'))


def do_local_preparation(veil_env_name):
    check_no_changes_not_committed()
    check_no_commits_not_pushed()
    check_no_migration_scripts_not_locked()
    check_no_locked_migration_scripts_changed()
    display_deployment_memo(veil_env_name)
    update_branch(veil_env_name)


def display_deployment_memo(veil_env_name):
    deployment_memo = get_veil_env_deployment_memo(veil_env_name)
    if deployment_memo:
        print('!!! IMPORTANT !!!')
        print(deployment_memo)
        print('type "i will do it" without space to continue:')
        while True:
            if 'iwilldoit' == sys.stdin.readline().strip():
                break


@script('rollback-env')
def rollback_env(veil_env_name):
    hosts = [host for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name) if is_rollbackable(host)]
    if hosts:
        stop_env(veil_env_name, True, False)
        rollback(hosts)
        start_env(veil_env_name)
        remove_rollbackable_tags(veil_env_name)
    else:
        print(yellow('No rollbackable hosts'))


def is_rollbackable(host):
    rollback_backup_dir = '{}-backup'.format(host.env_dir)
    with fabric.api.settings(host_string=host.deploys_via):
        if fabric.contrib.files.exists(host.rollbackable_tag_path) and fabric.contrib.files.exists(rollback_backup_dir):
            return True
        else:
            print(yellow('Host {} is not rollbackable: no rollbackable tag or no rollback backup'.format(host.base_name)))
            return False


def rollback(hosts):
    ensure_servers_down(hosts)
    for host in hosts:
        source_dir = host.env_dir
        rollback_backup_dir = '{}-backup'.format(source_dir)
        with fabric.api.settings(host_string=host.deploys_via):
            if fabric.contrib.files.exists(source_dir):
                left_over_dir = '{}-to-be-deleted-{}'.format(source_dir, datetime.now().strftime('%Y%m%d%H%M%S'))
                fabric.api.sudo('rsync -ah --numeric-ids --delete --link-dest={}/ {}/ {}/'.format(rollback_backup_dir, source_dir, left_over_dir))
            fabric.api.sudo('rsync -ah --numeric-ids --delete {}/ {}/'.format(rollback_backup_dir, source_dir))


def ensure_servers_down(hosts):
    for host in hosts:
        with fabric.api.settings(host_string=host.deploys_via):
            ret = fabric.api.run('ps -ef | grep supervisord | grep {} | grep -v grep'.format(host.etc_dir), warn_only=True)
            if ret.return_code == 0:
                raise Exception('{}: can not rollback while having running veil server(s)'.format(host.base_name))


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
def stop_env(veil_env_name, include_guard_server=True, include_monitor_server=True):
    """
    Bring down veil servers in sorted server names order
    """
    if isinstance(include_guard_server, basestring):
        include_guard_server = include_guard_server == 'TRUE'
    if isinstance(include_monitor_server, basestring):
        include_monitor_server = include_monitor_server == 'TRUE'
    stop_servers(list_veil_servers(veil_env_name, include_guard_server, include_monitor_server))


def stop_servers(servers):
    for server in servers:
        if not is_server_running(server, not_on_host=True):
            continue
        with fabric.api.settings(host_string=server.deploys_via):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} down'.format(server.fullname))


@script('start-env')
def start_env(veil_env_name):
    """
    Bring up veil servers in reversed sorted server names order
    """
    for server in reversed(list_veil_servers(veil_env_name)):
        host = get_veil_host(server.env_name, server.host_name)
        with fabric.api.settings(host_string=host.deploys_via):
            if not fabric.contrib.files.exists(server.deployed_tag_path):
                print(yellow('Skipped starting server {} as it is not successfully deployed'.format(server.container_name)))
                continue
            if is_server_running(server):
                continue
            if is_container_running(server):
                with fabric.api.settings(host_string=server.deploys_via):
                    with fabric.api.cd(server.veil_home):
                        fabric.api.sudo('veil :{} up --daemonize'.format(server.fullname))
            else:
                fabric.api.sudo('lxc-start -n {} -d'.format(server.container_name))


@script('upgrade-env-pip')
def upgrade_env_pip(veil_env_name, setuptools_version, pip_version):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        with fabric.api.settings(host_string=host.deploys_via):
            with fabric.api.cd(host.veil_home):
                fabric.api.sudo('veil :{} upgrade-pip {} {}'.format(host.env_name, setuptools_version, pip_version))


def get_deployed_at():
    last_commit = shell_execute('git rev-parse HEAD', capture=True)
    lines = shell_execute("git show-ref --tags -d | grep ^{} | sed -e 's,.* refs/tags/,,' -e 's/\^{{}}//'".format(last_commit), capture=True)
    deployed_ats = []
    for tag in lines.splitlines(False):
        env_name, formatted_deployed_at, _ = tag.rsplit('-', 2)
        if env_name == VEIL_ENV_NAME:
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
    tag_name = '{}-{}-{}'.format(veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))


def tag_patch(veil_env_name):
    tag_name = '{}-{}-{}-patch'.format(
        veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))
