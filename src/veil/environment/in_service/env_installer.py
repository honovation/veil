# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import time
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
from veil.environment.lxd import *
from veil.utility.clock import *
from veil.utility.shell import *
from veil.backend.database.migration import *
from .host_installer import veil_hosts_resource, veil_hosts_codebase_resource, veil_host_codebase_resource
from .server_installer import veil_servers_resource, is_container_running, is_server_running
from .env_config_dir import set_env_config_dir, get_env_config_dir


@script('deploy-env')
@log_elapsed_time
def deploy_env(veil_env_name, config_dir, should_download_packages='TRUE', include_monitor_server='TRUE', start_after_deploy='TRUE',
               disable_external_access_='FALSE'):
    """
    注意：
    start_after_deploy不是'TRUE'，指的是deploy后服务不是启动状态，并不意味着在部署过程中服务不会启动。比如，在安装
    veil host resource的过程中，当lxc配置有变动时会重启/启动容器进而启动服务，当lxc配置没有变动且容器没有启动时也会
    启动容器进而启动服务。
    所以，不能依赖start_after_deploy不是'TRUE'来保证worker没有启动以避免多veil env下worker服务同时处理任务可能造
    成的问题。这个问题只能依赖特性“worker只有在redis的reserve_job和当前veil env一致时才处理任务”去避免。
    """
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    print(cyan('Update config ...'))
    update_config(config_dir)
    print(cyan('Make local preparation ...'))
    do_local_preparation(veil_env_name)
    print(cyan('Tag deploy ...'))
    tag_deploy(veil_env_name)

    print(cyan('Make rollback backup -- include code dir, exclude data dir ...'))
    make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True)
    print(cyan('Deploy hosts ...'))
    install_resource(veil_hosts_resource(veil_env_name=veil_env_name))
    if disable_external_access_ == 'TRUE':
        print(cyan('Disable external access ...'))
        disable_external_access(veil_env_name)

    if should_download_packages == 'TRUE':
        print(cyan('Download packages ...'))
        download_packages(veil_env_name)

    first_round_servers = []
    second_round_servers = []
    for server in list_veil_servers(veil_env_name):
        if not server.is_guard and not server.is_barman and not server.is_monitor:
            first_round_servers.append(server)
        else:
            if not server.is_monitor or include_monitor_server == 'TRUE':
                second_round_servers.append(server)

    if first_round_servers:
        start_time = time.time()
        first_round_server_names = [server.name for server in first_round_servers]
        print(cyan('Stop round-1 servers {} ...'.format(first_round_server_names)))
        stop_servers(first_round_servers)
        print(cyan('Make rollback backup -- exclude code dir, include data dir ...'))
        make_rollback_backup(veil_env_name, exclude_code_dir=True, exclude_data_dir=False)
        print(cyan('Deploy round-1 servers {} ...'.format(first_round_server_names[::-1])))
        install_resource(veil_servers_resource(servers=first_round_servers[::-1], action='DEPLOY', start_after_deploy=start_after_deploy == 'TRUE'))
        elapsed_seconds_to_deploy_first_round_servers = time.time() - start_time
        print(cyan('\nElapsed time for deploying round-1 servers: {} seconds\n'.format(elapsed_seconds_to_deploy_first_round_servers)))
    else:
        elapsed_seconds_to_deploy_first_round_servers = None
        print(cyan('No round-1 servers to deploy'))

    if second_round_servers:
        second_round_server_names = [server.name for server in second_round_servers]
        print(cyan('Stop round-2 servers {} ...'.format(second_round_server_names)))
        stop_servers(second_round_servers)
        print(cyan('Deploy round-2 servers {} ...'.format(second_round_server_names[::-1])))
        install_resource(veil_servers_resource(servers=second_round_servers[::-1], action='DEPLOY', start_after_deploy=start_after_deploy == 'TRUE'))
    else:
        print(cyan('No round-2 servers to deploy'))

    print(cyan('Remove rollbackable tags ...'))
    remove_rollbackable_tags(veil_env_name)

    print(cyan('Enable vm.overcommit_memory on redis-server-running hosts ...'))
    enable_vm_overcommit_memory_on_redis_server_running_hosts(veil_env_name)

    if elapsed_seconds_to_deploy_first_round_servers:
        print(cyan('\nElapsed time for deploying round-1 servers: {} seconds\n'.format(elapsed_seconds_to_deploy_first_round_servers)))


def enable_vm_overcommit_memory_on_redis_server_running_hosts(veil_env_name):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            fabric.api.sudo('ps -ef | grep redis-server | grep -v grep && sysctl vm.overcommit_memory=1',
                            warn_only=True)


def make_rollback_backup(veil_env_name, exclude_code_dir=False, exclude_data_dir=True):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        source_dir = host.env_dir
        rollback_backup_dir = '{}-backup'.format(source_dir)
        excludes = []
        if exclude_code_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.code_dir)))
        if exclude_data_dir:
            excludes.append('--exclude "/{}"'.format(host.env_dir.relpathto(host.data_dir)))
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            if not fabric.contrib.files.exists(source_dir):
                continue
            fabric.api.sudo(
                'rsync -ah --numeric-ids --delete {} --link-dest={}/ {}/ {}/'.format(' '.join(excludes), source_dir, source_dir, rollback_backup_dir))
            fabric.api.sudo('touch {}'.format(host.rollbackable_tag_path))


def remove_rollbackable_tags(veil_env_name):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            fabric.api.sudo('rm -f {}'.format(host.rollbackable_tag_path))


@script('download-packages')
def download_packages(veil_env_name):
    # this command should not interrupt normal website operation
    # designed to run when website is still running, to prepare for a full deployment
    for host in list_veil_hosts(veil_env_name):
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            with fabric.api.cd(host.veil_home):
                with fabric.api.settings(forward_agent=True):
                    while True:
                        try:
                            fabric.api.run('git archive --format=tar --remote=origin master RESOURCE-LATEST-VERSION-* | tar -x')
                        except Exception as e:
                            print(red('Git archive failed, retry: {}'.format(e.message)))
                        else:
                            break
                try:
                    for server in host.server_list:
                        print(cyan('Download packages for server {} ...'.format(server.name)))
                        if not fabric.contrib.files.exists(server.deployed_tag_path):
                            print(yellow('Skipped downloading packages for server {} as it is not successfully deployed'.format(server.container_name)))
                            continue
                        if not is_container_running(server):
                            print(yellow('Skipped downloading packages for server {} as its container is not running'.format(server.container_name)))
                            continue
                        with fabric.api.settings(host_string=server.deploys_via, user=server.ssh_user, port=server.ssh_port):
                            with fabric.api.cd(server.veil_home):
                                fabric.api.run('veil :{} install-server --download-only'.format(server.fullname))
                finally:
                    fabric.api.run('git checkout -- RESOURCE-LATEST-VERSION-*')


@script('deploy-monitor')
@log_elapsed_time
def deploy_monitor(veil_env_name, config_dir):
    _deploy_server(veil_env_name, config_dir, 'monitor')


@script('deploy-guard')
@log_elapsed_time
def deploy_guard(veil_env_name, config_dir):
    for server in list_veil_servers(veil_env_name):
        if not server.is_guard:
            continue
        _deploy_server(veil_env_name, config_dir, server.name)


@script('deploy-barman')
@log_elapsed_time
def deploy_barman(veil_env_name, config_dir):
    _deploy_server(veil_env_name, config_dir, 'barman')


@script('deploy-server')
@log_elapsed_time
def deploy_server(veil_env_name, config_dir, veil_server_name):
    _deploy_server(veil_env_name, config_dir, veil_server_name)


def _deploy_server(veil_env_name, config_dir, veil_server_name):
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    server = get_veil_server(veil_env_name, veil_server_name)
    host = get_veil_host(veil_env_name, server.host_name)
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        if not fabric.contrib.files.exists(server.deployed_tag_path):
            print(yellow('Use deploy-env to deploy {} first time'.format(veil_server_name)))
            return
        install_resource(veil_host_codebase_resource(host=host))
    stop_servers([server])
    install_resource(veil_servers_resource(servers=[server], action='DEPLOY'))


@script('patch-env')
@log_elapsed_time
def patch_env(veil_env_name, config_dir):
    """
    Iterate veil server in reversed sorted server names order (in veil_servers_resource and local_deployer:patch)
        and patch programs
    """
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    print(cyan('Make local preparation ...'))
    do_local_preparation(veil_env_name)
    print(cyan('Tag patch ...'))
    tag_patch(veil_env_name)
    print(cyan('Pull codebase ...'))
    install_resource(veil_hosts_codebase_resource(veil_env_name=veil_env_name))
    servers = list_veil_servers(veil_env_name, include_guard_server=False, include_monitor_server=False, include_barman_server=False)
    server_names = [s.name for s in servers]
    print(cyan('Patch servers {} ...'.format(server_names[::-1])))
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
def rollback_env(veil_env_name, config_dir):
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    hosts = [host for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name) if is_rollbackable(host)]
    if hosts:
        stop_env(veil_env_name, config_dir, include_guard_server=True, include_monitor_server=False, include_barman_server=False)
        rollback(hosts)
        start_env(veil_env_name, config_dir)
        remove_rollbackable_tags(veil_env_name)
    else:
        print(yellow('No rollbackable hosts'))


def is_rollbackable(host):
    rollback_backup_dir = '{}-backup'.format(host.env_dir)
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
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
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            if fabric.contrib.files.exists(source_dir):
                left_over_dir = '{}-to-be-deleted-{}'.format(source_dir, datetime.now().strftime('%Y%m%d%H%M%S'))
                fabric.api.sudo('rsync -ah --numeric-ids --delete --link-dest={}/ {}/ {}/'.format(rollback_backup_dir, source_dir, left_over_dir))
            fabric.api.sudo('rsync -ah --numeric-ids --delete {}/ {}/'.format(rollback_backup_dir, source_dir))


def ensure_servers_down(hosts):
    for host in hosts:
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            ret = fabric.api.run('ps -ef | grep supervisord | grep {} | grep -v monitor | grep -v grep'.format(host.etc_dir), warn_only=True)
            if ret.return_code == 0:
                raise Exception('{}: can not rollback while having running veil server(s)'.format(host.base_name))


@script('backup-env')
def backup_env(veil_env_name):
    for server in list_veil_servers(veil_env_name):
        if not server.is_guard:
            continue
        with fabric.api.settings(host_string=server.deploys_via, user=server.ssh_user, port=server.ssh_port):
            with fabric.api.cd(server.veil_home):
                fabric.api.sudo('veil :{} backup-host'.format(server.fullname))


@script('purge-left-overs')
def purge_left_overs(veil_env_name):
    hosts = unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name)
    for host in hosts:
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            fabric.api.sudo('rm -rf {}-to-be-deleted-*'.format(host.env_dir))


@script('restart-env')
def restart_env(veil_env_name, config_dir, disable_external_access_='FALSE', *exclude_server_names):
    """
    Bring down veil servers in sorted server names order
    Bring up veil servers in reversed sorted server names order
    """
    stop_env(veil_env_name, config_dir)
    start_env(veil_env_name, config_dir, disable_external_access_, *exclude_server_names)


@script('stop-env')
def stop_env(veil_env_name, config_dir, include_guard_server=True, include_monitor_server=True, include_barman_server=True, *exclude_server_names):
    """
    Bring down veil servers in sorted server names order
    """
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    if isinstance(include_guard_server, basestring):
        include_guard_server = include_guard_server == 'TRUE'
    if isinstance(include_monitor_server, basestring):
        include_monitor_server = include_monitor_server == 'TRUE'
    servers = []
    for server in list_veil_servers(veil_env_name, include_guard_server=include_guard_server, include_monitor_server=include_monitor_server,
                                    include_barman_server=include_barman_server):
        if exclude_server_names and server.name in exclude_server_names:
            continue
        servers.append(server)
    stop_servers(servers, stop_container=True)


def stop_servers(servers, stop_container=False):
    for server in servers:
        host = get_veil_host(server.VEIL_ENV.name, server.host_name)
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            if is_container_running(server):
                while is_server_running(server):
                    print(cyan('Stop server {} ...'.format(server.name)))
                    with fabric.api.settings(host_string=server.deploys_via, user=server.ssh_user, port=server.ssh_port):
                        fabric.api.sudo('systemctl stop veil-server.service')
                    time.sleep(1)
                if stop_container:
                    container = LXDClient(endpoint=server.lxd_endpoint, config_dir=get_env_config_dir()).get_container(server.container_name)
                    container.stop()


@script('start-env')
def start_env(veil_env_name, config_dir, disable_external_access_='FALSE', *exclude_server_names):
    """
    Bring up veil servers in reversed sorted server names order
    """
    set_env_config_dir(as_path(config_dir) / veil_env_name)
    if disable_external_access_ == 'TRUE':
        print(cyan('Disable external access ...'))
        disable_external_access(veil_env_name)

    for server in reversed(list_veil_servers(veil_env_name)):
        if server.name in exclude_server_names:
            continue
        host = get_veil_host(server.VEIL_ENV.name, server.host_name)
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            if not fabric.contrib.files.exists(server.deployed_tag_path):
                print(yellow('Skipped starting server {} as it is not successfully deployed'.format(server.container_name)))
                continue
            if is_container_running(server):
                while not is_server_running(server):
                    print(cyan('Start server {} ...'.format(server.name)))
                    with fabric.api.settings(host_string=server.deploys_via, user=server.ssh_user, port=server.ssh_port):
                        fabric.api.sudo('systemctl start veil-server.service')
                    time.sleep(1)
            else:
                container = LXDClient(endpoint=server.lxd_endpoint, config_dir=get_env_config_dir()).get_container(server.container_name)
                container.start()


@script('disable-external-access')
def disable_external_access_script(veil_env_name):
    disable_external_access(veil_env_name)


def disable_external_access(veil_env_name):
    for host in list_veil_hosts(veil_env_name):
        if not host.external_service_ports:
            continue
        external_service_ports = ','.join(str(p) for p in host.external_service_ports)
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            check_result = fabric.api.sudo('iptables -w -t nat -C PREROUTING -p tcp -m multiport --dports {} -j RETURN'.format(external_service_ports),
                                           warn_only=True)
            if check_result.failed:
                fabric.api.sudo('iptables -w -t nat -I PREROUTING 1 -p tcp -m multiport --dports {} -j RETURN'.format(external_service_ports))
            print(cyan('DISABLED {}: {}'.format(host.base_name, host.external_service_ports)))


@script('enable-external-access')
def enable_external_access_script(veil_env_name):
    enable_external_access(veil_env_name)


def enable_external_access(veil_env_name):
    for host in list_veil_hosts(veil_env_name):
        if not host.external_service_ports:
            continue
        external_service_ports = ','.join(str(p) for p in host.external_service_ports)
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            while 1:
                check_result = fabric.api.sudo('iptables -w -t nat -C PREROUTING -p tcp -m multiport --dports {} -j RETURN'.format(external_service_ports),
                                               warn_only=True)
                if check_result.failed:
                    break
                fabric.api.sudo('iptables -w -t nat -D PREROUTING -p tcp -m multiport --dports {} -j RETURN'.format(external_service_ports), warn_only=True)
            print(green('ENABLED {}: {}'.format(host.base_name, host.external_service_ports)))


@script('upgrade-env-pip')
def upgrade_env_pip(veil_env_name, setuptools_version, wheel_version, pip_version):
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            with fabric.api.cd(host.veil_home):
                fabric.api.sudo('veil :{} upgrade-pip {} {} {}'.format(host.VEIL_ENV.name, setuptools_version, wheel_version, pip_version))


def get_deployed_or_patched_at():
    """
        tag format:
            APP-ENV-TIMESTAMP-UUID[-patch]

        exmaples:
            deploy tag: app-public--3-20140829142721-cb557ad92be8eea70c4ec9bf45321026c5e18d56
            or
            patch tag: app-public--3-20140829142721-cb557ad92be8eea70c4ec9bf45321026c5e18d56-patch
    """
    last_commit = shell_execute('git rev-parse HEAD', capture=True)
    lines = shell_execute("git show-ref --tags -d | grep ^{} | sed -e 's,.* refs/tags/,,'".format(last_commit), capture=True)
    deployed_or_patched_at = []
    for tag in lines.splitlines():
        if tag.endswith('-patch'):
            tag = tag[:-len('-patch')]
        env_name, formatted_deployed_at, _ = tag.rsplit('-', 2)
        if env_name == VEIL_ENV.name:
            deployed_or_patched_at.append(convert_datetime_to_client_timezone(datetime.strptime(formatted_deployed_at, '%Y%m%d%H%M%S')))
    return max(deployed_or_patched_at) if deployed_or_patched_at else None


def update_config(config_dir):
    shell_execute('git pull --rebase', cwd=config_dir)


def update_branch(veil_env_name):
    print('update env-{} branch...'.format(veil_env_name))
    try:
        shell_execute('git checkout -B env-{}'.format(veil_env_name), cwd=VEIL_HOME)
        shell_execute('git merge master --ff-only', cwd=VEIL_HOME)
        shell_execute('git push origin env-{}'.format(veil_env_name), cwd=VEIL_HOME)

        # check remote consistency after push
        shell_execute('git fetch origin', cwd=VEIL_HOME)
        if bool(shell_execute('git diff origin/env-{}'.format(veil_env_name), capture=True, cwd=VEIL_HOME)):
            raise Exception('Found remote inconsistency in branch: env-{}'.format(veil_env_name))
    finally:
        shell_execute('git checkout master', cwd=VEIL_HOME)


def tag_deploy(veil_env_name):
    tag_name = '{}-{}-{}'.format(veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))


def tag_patch(veil_env_name):
    tag_name = '{}-patch-{}-{}'.format(veil_env_name, get_current_time_in_client_timezone().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))
