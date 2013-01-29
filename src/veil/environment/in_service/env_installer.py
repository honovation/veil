from __future__ import unicode_literals, print_function, division
import fabric.api
import os
import logging
import datetime
import sys
from veil.utility.path import *
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from .container_installer import veil_env_containers_resource
from .server_installer import veil_env_servers_resource

PAYLOAD = os.path.join(os.path.dirname(__file__), 'env_installer_payload.py')
LOGGER = logging.getLogger(__name__)

@script('update-env-authorized-keys')
def update_env_authorized_keys(veil_env_name, config_dir):
    veil_hosts = list_veil_hosts(veil_env_name)
    for veil_host_name, veil_host in veil_hosts.items():
        veil_host_name = veil_host_name.split('/')[0] # ljhost-005/3 => ljhost-005
        authorized_keys_path = as_path(config_dir) / 'host' / veil_host_name / 'authorized_keys'
        fabric.state.env.host_string = '{}:{}'.format(veil_host.internal_ip, veil_host.ssh_port)
        fabric.api.put(authorized_keys_path, '~/.ssh/authorized_keys')


@script('deploy-env')
def deploy_env(veil_env_name, config_dir):
    deployment_memo = get_veil_env_deployment_memo(veil_env_name)
    if deployment_memo:
        print('!!! IMPORTANT !!!')
        print(deployment_memo)
        print('type "i will do it" without space to continue:')
        while True:
            if 'iwilldoit' == sys.stdin.readline().strip():
                break
    check_locked_all_scripts()
    update_branch(veil_env_name)
    install_resource(veil_env_containers_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('create-backup', veil_env_name, deploying_server_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name))
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('delete-backup', veil_env_name, deploying_server_name)
    tag_deploy(veil_env_name)


@script('patch-env')
def patch_env(veil_env_name):
    check_locked_all_scripts()
    update_branch(veil_env_name)
    install_resource(veil_env_servers_resource(veil_env_name=veil_env_name, is_patch=True))
    tag_patch(veil_env_name)


@script('rollback-env')
def rollback_env(vel_env_name):
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('check-backup', vel_env_name, veil_server_name)
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('rollback', vel_env_name, veil_server_name)
    for veil_server_name in sorted(list_veil_servers(vel_env_name).keys()):
        remote_do('delete-backup', vel_env_name, veil_server_name)


@script('purge-left-overs')
def purge_left_overs(veil_env_name):
    for veil_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('purge-left-overs', veil_env_name, veil_server_name)


def remote_do(action, veil_env_name, veil_server_name):
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.api.put(PAYLOAD, '/opt/env_installer_payload.py', use_sudo=True, mode=0600)
    fabric.api.sudo('python /opt/env_installer_payload.py {} {} {}'.format(
        action,
        veil_env_name,
        veil_server_name))


def update_branch(veil_env_name):
    LOGGER.info('update env-{} branch...'.format(veil_env_name))
    shell_execute('git checkout env-{}'.format(veil_env_name), cwd=VEIL_HOME)
    shell_execute('git merge master --ff-only', cwd=VEIL_HOME)
    shell_execute('git push origin env-{}'.format(veil_env_name), cwd=VEIL_HOME)
    shell_execute('git checkout master', cwd=VEIL_HOME)


def tag_deploy(veil_env_name):
    tag_name = '{}-{}-{}'.format(
        veil_env_name, datetime.datetime.now().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))

def tag_patch(veil_env_name):
    tag_name = '{}-{}-{}-patch'.format(
        veil_env_name, datetime.datetime.now().strftime('%Y%m%d%H%M%S'), get_veil_framework_version())
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

def check_locked_all_scripts():
    migration_script_dir = VEIL_HOME / 'db'
    purposes = migration_script_dir.listdir()
    for purpose in purposes:
        locked_file_count = len(purpose.listdir('*.locked'))
        script_file_count = len(purpose.listdir('*.sql'))
        if locked_file_count < script_file_count:
            print(red('You must lock scripts in {}'.format(purpose)))
            return
        else:
            print(green('Migration script check in {} ...passed!'.format(purpose)))