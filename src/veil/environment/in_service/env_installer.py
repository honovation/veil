from __future__ import unicode_literals, print_function, division
import fabric.api
import os
import logging
from datetime import datetime
import sys
from veil_component import *
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.clock import *
from veil.utility.shell import *
from veil.backend.database.postgresql import *
from .host_installer import veil_env_hosts_resource
from .container_installer import veil_env_containers_resource
from .server_installer import veil_env_servers_resource

LOGGER = logging.getLogger(__name__)

PAYLOAD = os.path.join(os.path.dirname(__file__), 'env_installer_payload.py')

def display_deployment_memo(veil_env_name):
    deployment_memo = get_veil_env_deployment_memo(veil_env_name)
    if deployment_memo:
        print('!!! IMPORTANT !!!')
        print(deployment_memo)
        print('type "i will do it" without space to continue:')
        while True:
            if 'iwilldoit' == sys.stdin.readline().strip():
                break


@script('deploy-env')
def deploy_env(veil_env_name, config_dir, should_download_packages='TRUE'):
    """ should_download_packages: set to FALSE when download-packages before deploy-env """
    do_local_preparation(veil_env_name)
    tag_deploy(veil_env_name)
    install_resource(veil_env_hosts_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    install_resource(veil_env_containers_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    if 'TRUE' == should_download_packages:
        download_packages(veil_env_name)
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('create-backup', veil_env_name, deploying_server_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name, action='DEPLOY'))
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('delete-backup', veil_env_name, deploying_server_name)


@script('download-packages')
def download_packages(veil_env_name):
    # this command should not interrupt normal website operation
    # designed to run when website is still running, to prepare for a full deployment
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('download-packages', veil_env_name, deploying_server_name)


@script('patch-env')
def patch_env(veil_env_name):
    do_local_preparation(veil_env_name)
    tag_patch(veil_env_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name, action='PATCH'))


def do_local_preparation(veil_env_name):
    display_deployment_memo(veil_env_name)
    check_all_locked_migration_scripts()
    check_if_locked_migration_scripts_being_changed()
    update_branch(veil_env_name)


@script('rollback-env')
def rollback_env(vel_env_name):
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('check-backup', vel_env_name, veil_server_name)
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('rollback', vel_env_name, veil_server_name)
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('delete-backup', vel_env_name, veil_server_name)


@script('backup-env')
def backup_env(veil_env_name, should_bring_up_servers='TRUE', veil_guard_name='@guard'):
    deployed_via = get_veil_server_deploys_via(veil_env_name, veil_guard_name)
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(veil_env_name)):
        fabric.api.sudo('veil :{}/{} backup-env {}'.format(veil_env_name, veil_guard_name, should_bring_up_servers))


@script('purge-left-overs')
def purge_left_overs(veil_env_name):
    for veil_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('purge-left-overs', veil_env_name, veil_server_name)


@script('print-deployed-at')
def print_deployed_at():
    print(get_deployed_at())


def get_deployed_at():
    last_commit = shell_execute('git rev-parse HEAD', capture=True).strip()
    lines = shell_execute("git show-ref --tags -d | grep ^%s | sed -e 's,.* refs/tags/,,' -e 's/\^{}//'" % last_commit,
        shell=True, capture=True)
    deployed_ats = []
    for tag in lines.splitlines(False):
        if tag.startswith('{}-'.format(VEIL_ENV)):
            formatted_deployed_at = tag.replace('{}-'.format(VEIL_ENV), '').split('-')[0]
            deployed_ats.append(convert_datetime_to_client_timezone(datetime.strptime(formatted_deployed_at, '%Y%m%d%H%M%S')))
    return max(deployed_ats) if deployed_ats else None


def remote_do(action, veil_env_name, veil_server_name):
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.api.put(PAYLOAD, '/opt/env_installer_payload.py', use_sudo=True, mode=0600)
    fabric.api.sudo('python /opt/env_installer_payload.py {} {} {}'.format(action, veil_env_name, veil_server_name))


def update_branch(veil_env_name):
    LOGGER.info('update env-%(env)s branch...', {'env': veil_env_name})
    shell_execute('git checkout env-{}'.format(veil_env_name), cwd=VEIL_HOME)
    shell_execute('git merge master --ff-only', cwd=VEIL_HOME)
    shell_execute('git push origin env-{}'.format(veil_env_name), cwd=VEIL_HOME)
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
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')