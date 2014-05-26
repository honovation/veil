from __future__ import unicode_literals, print_function, division
import fabric.api
import fabric.contrib.files
import os
from datetime import datetime
import sys
from veil.development.git import *
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.clock import *
from veil.utility.shell import *
from veil.backend.database.migration import *
from .host_installer import veil_env_hosts_resource
from .container_installer import veil_env_containers_resource
from .server_installer import veil_env_servers_resource

PAYLOAD = os.path.join(os.path.dirname(__file__), 'env_installer_payload.py')
veil_servers_with_payload_uploaded = []


def display_deployment_memo(veil_env_name):
    deployment_memo = get_veil_env_deployment_memo(veil_env_name)
    if deployment_memo:
        print('!!! IMPORTANT !!!')
        print(deployment_memo)
        print('type "i will do it" without space to continue:')
        while True:
            if 'iwilldoit' == sys.stdin.readline().strip():
                break


def is_veil_env_deployed(veil_env_name):
    veil_server_deployed_file_path = '/opt/deployed'
    for veil_server_name in list_veil_server_names(veil_env_name):
        fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
        if not fabric.contrib.files.exists(veil_server_deployed_file_path, use_sudo=True):
            return False
    return True


@script('deploy-env')
def deploy_env(veil_env_name, config_dir, should_download_packages='TRUE'):
    """
    Bring down veil servers in sorted server names order (in create-backup)
    Bring up veil servers in reversed sorted server names order (in veil_env_servers_resource and local_deployer:deploy)

    should_download_packages: set to FALSE when download-packages before deploy-env
    """
    do_local_preparation(veil_env_name)
    tag_deploy(veil_env_name)
    install_resource(veil_env_hosts_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    install_resource(veil_env_containers_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    veil_server_names = list_veil_server_names(veil_env_name)
    is_deployed = is_veil_env_deployed(veil_env_name)
    if is_deployed:
        if 'TRUE' == should_download_packages:
            download_packages(veil_env_name)
        for deploying_server_name in veil_server_names:
            remote_do('create-backup', veil_env_name, deploying_server_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name, action='DEPLOY'))
    if is_deployed:
        for deploying_server_name in veil_server_names:
            remote_do('delete-backup', veil_env_name, deploying_server_name)


@script('download-packages')
def download_packages(veil_env_name):
    # this command should not interrupt normal website operation
    # designed to run when website is still running, to prepare for a full deployment
    for deploying_server_name in list_veil_server_names(veil_env_name):
        remote_do('download-packages', veil_env_name, deploying_server_name)


@script('patch-env')
def patch_env(veil_env_name):
    """
    Iterate veil server in reversed sorted server names order (in veil_env_servers_resource and local_deployer:patch)
        and patch programs
    """
    do_local_preparation(veil_env_name)
    tag_patch(veil_env_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name, action='PATCH'))


def do_local_preparation(veil_env_name):
    check_no_local_changes()
    check_all_local_commits_pushed()
    check_all_locked_migration_scripts()
    check_if_locked_migration_scripts_being_changed()
    display_deployment_memo(veil_env_name)
    update_branch(veil_env_name)


@script('rollback-env')
def rollback_env(veil_env_name):
    """
    Bring down veil servers in sorted server names order (in rollback)
    Bring up veil servers in reversed sorted server names order
    """
    veil_server_names = list_veil_server_names(veil_env_name)
    for veil_server_name in veil_server_names:
        remote_do('check-backup', veil_env_name, veil_server_name)
    for veil_server_name in veil_server_names:
        remote_do('rollback', veil_env_name, veil_server_name)
    start_env(veil_env_name)
    for veil_server_name in veil_server_names:
        remote_do('delete-backup', veil_env_name, veil_server_name)


@script('backup-env')
def backup_env(veil_env_name, should_bring_up_servers='TRUE', veil_guard_name='@guard'):
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_guard_name)
    with fabric.api.cd('/opt/{}/app'.format(veil_env_name)):
        fabric.api.sudo('veil :{}/{} backup-env {}'.format(veil_env_name, veil_guard_name, should_bring_up_servers))


@script('purge-left-overs')
def purge_left_overs(veil_env_name):
    for veil_server_name in list_veil_server_names(veil_env_name):
        remote_do('purge-left-overs', veil_env_name, veil_server_name)


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
    for veil_server_name in list_veil_server_names(veil_env_name):
        remote_do('bring-down-server', veil_env_name, veil_server_name)


@script('start-env')
def start_env(veil_env_name):
    """
    Bring up veil servers in reversed sorted server names order
    """
    for veil_server_name in reversed(list_veil_server_names(veil_env_name)):
        remote_do('bring-up-server', veil_env_name, veil_server_name)


@script('upgrade-env-pip')
def upgrade_env_pip(veil_env_name, setuptools_version, pip_version):
    """
    Upgrade pip and setuptools on veil servers
    """
    for veil_server_name in list_veil_server_names(veil_env_name):
        remote_do('upgrade-pip', veil_env_name, veil_server_name, pip_version, setuptools_version)


@script('print-deployed-at')
def print_deployed_at():
    print(get_deployed_at())


def get_deployed_at():
    last_commit = shell_execute('git rev-parse HEAD', capture=True)
    lines = shell_execute("git show-ref --tags -d | grep ^{} | sed -e 's,.* refs/tags/,,' -e 's/\^{{}}//'".format(last_commit), capture=True)
    deployed_ats = []
    for tag in lines.splitlines(False):
        if tag.startswith('{}-'.format(VEIL_ENV)):
            formatted_deployed_at = tag.replace('{}-'.format(VEIL_ENV), '').split('-')[0]
            deployed_ats.append(convert_datetime_to_client_timezone(datetime.strptime(formatted_deployed_at, '%Y%m%d%H%M%S')))
    return max(deployed_ats) if deployed_ats else None


def remote_do(action, veil_env_name, veil_server_name, *args):
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.api.env.forward_agent = True
    if fabric.api.env.host_string not in veil_servers_with_payload_uploaded:
        fabric.api.put(PAYLOAD, '/opt/env_installer_payload.py', use_sudo=True, mode=0600)
        veil_servers_with_payload_uploaded.append(fabric.api.env.host_string)
    fabric.api.sudo('python /opt/env_installer_payload.py {} {} {} {}'.format(action, veil_env_name, veil_server_name, ' '.join(arg for arg in args)))


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


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = '1;{}'.format(c)
        return '\033[{}m{}\033[0m'.format(c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')