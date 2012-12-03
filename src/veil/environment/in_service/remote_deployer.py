from __future__ import unicode_literals, print_function, division
import logging
import os
import datetime
import fabric.api
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from .host_installer import provision_env

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_deployer_payload.py')
GUARD = os.path.join(os.path.dirname(__file__), 'remote_deployer_guard.py')
LOGGER = logging.getLogger(__name__)

@atomic_installer
def veil_env_in_service_resource(name, config_dir):
    provision_env(name, config_dir)
    deploy_env(name)


@script('deploy-env')
def deploy_env(deploying_env):
    update_branch(deploying_env)
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('create-backup', deploying_env, deploying_server_name)
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        deploy_server(deploying_env, deploying_server_name)
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('delete-backup', deploying_env, deploying_server_name)
    tag_deploy(deploying_env)


@script('rollback-env')
def rollback_env(deploying_env):
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('check-backup', deploying_env, deploying_server_name)
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('rollback', deploying_env, deploying_server_name)
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('delete-backup', deploying_env, deploying_server_name)


@script('purge-left-overs')
def purge_left_overs(deploying_env):
    for deploying_server_name in sorted(get_veil_servers(deploying_env).keys()):
        guard_do('purge-left-overs', deploying_env, deploying_server_name)


def guard_do(action, deploying_env, deploying_server_name):
    deployed_via = get_remote_veil_server(deploying_env, deploying_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    fabric.api.put(GUARD, '/opt/remote_deployer_guard.py', use_sudo=True, mode=0700)
    fabric.api.sudo('python /opt/remote_deployer_guard.py {} {} {}'.format(
        action,
        deploying_env,
        deploying_server_name))


def deploy_server(deploying_env, deploying_server_name):
    deployed_via = get_remote_veil_server(deploying_env, deploying_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    fabric.api.env.forward_agent = True
    fabric.api.put(PAYLOAD, '/opt/remote_deployer_payload.py', use_sudo=True, mode=0700)
    fabric.api.sudo('python /opt/remote_deployer_payload.py {} {} {}'.format(
        get_application_codebase(),
        deploying_env,
        deploying_server_name))


def update_branch(deploying_env):
    LOGGER.info('update env-{} branch...'.format(deploying_env))
    shell_execute('git checkout env-{}'.format(deploying_env), cwd=VEIL_HOME)
    shell_execute('git merge master --ff-only', cwd=VEIL_HOME)
    shell_execute('git push origin env-{}'.format(deploying_env), cwd=VEIL_HOME)
    shell_execute('git checkout master', cwd=VEIL_HOME)


def tag_deploy(deploying_env):
    tag_name = 'deploy-{}-{}'.format(deploying_env, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))