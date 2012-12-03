from __future__ import unicode_literals, print_function, division
import fabric.api
import os
import logging
import datetime
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from .container_installer import veil_env_containers_resource
from .server_installer import veil_env_servers_resource

PAYLOAD = os.path.join(os.path.dirname(__file__), 'env_installer_payload.py')
LOGGER = logging.getLogger(__name__)

@script('deploy-env')
def deploy_env(veil_env_name, config_dir):
    update_branch(veil_env_name)
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('create-backup', veil_env_name, deploying_server_name)
    do_install(veil_env_resource(veil_env_name=veil_env_name, config_dir=config_dir))
    for deploying_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        remote_do('delete-backup', veil_env_name, deploying_server_name)
    tag_deploy(veil_env_name)


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


@composite_installer
def veil_env_resource(veil_env_name, config_dir):
    resources = [
        veil_env_containers_resource(veil_env_name=veil_env_name, config_dir=config_dir),
        veil_env_servers_resource(veil_env_name=veil_env_name)]
    return resources


def remote_do(action, veil_env_name, veil_server_name):
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.api.put(PAYLOAD, '/opt/env_installer_payload.py', use_sudo=True, mode=0700)
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
    tag_name = 'deploy-{}-{}'.format(veil_env_name, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))