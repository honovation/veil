from __future__ import unicode_literals, print_function, division
import logging
from argparse import ArgumentParser
from fabric.colors import green
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
import os
import datetime
import fabric.api

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_deployer_payload.py')
LOGGER = logging.getLogger(__name__)

@script('deploy-env')
def deploy_env(deploying_env, from_branch=None):
    update_branch(deploying_env, from_branch)
    for veil_server_name in sorted(get_veil_servers(deploying_env).keys()):
        deploy_server('{}/{}'.format(deploying_env, veil_server_name))
    if not from_branch:
        tag_deploy(deploying_env)


@script('deploy-server')
def execute_deploy_server(*argv):
    argument_parser = ArgumentParser('Deploy a remote server')
    argument_parser.add_argument('remote_veil_server', type=str,
        help='remote VEIL_SERVER, of format VEIL_ENV/VEIL_SERVER_NAME')
    argument_parser.add_argument('--deployed-via', help='override how to access the server to deploy')
    args = argument_parser.parse_args(argv)
    deploy_server(args.remote_veil_server, args.deployed_via)


def deploy_server(remote_veil_server, deployed_via=None):
    deployed_via = deployed_via or get_remote_veil_server(remote_veil_server).deployed_via
    veil_server_env, veil_server_name = split_veil_server_code(remote_veil_server)
    fabric.api.env.host_string = deployed_via
    fabric.api.put(PAYLOAD, '/opt/remote_deployer_payload.py', use_sudo=True, mode=0700)
    local_env_config_dir = CURRENT_USER_HOME / '.{}'.format(veil_server_env)
    if local_env_config_dir.exists():
        for f in local_env_config_dir.listdir():
            fabric.api.put(f, '~', mode=0600)
    fabric.api.sudo('python /opt/remote_deployer_payload.py {} {} {} {}'.format(
        get_application_codebase(),
        '/opt/{}'.format(get_application_name()),
        veil_server_env, veil_server_name))


def update_branch(deploying_env, from_branch):
    from_branch = from_branch or 'master'
    LOGGER.info('update env-{} branch...'.format(deploying_env))
    shell_execute('git checkout env-{}'.format(deploying_env), cwd=VEIL_HOME)
    shell_execute('git merge {} --ff-only'.format(from_branch), cwd=VEIL_HOME)
    shell_execute('git push origin env-{}'.format(deploying_env), cwd=VEIL_HOME)
    shell_execute('git checkout {}'.format(from_branch), cwd=VEIL_HOME)


def tag_deploy(deploying_env):
    tag_name = 'deploy-{}-{}'.format(deploying_env, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    shell_execute('git tag {}'.format(tag_name))
    shell_execute('git push origin tag {}'.format(tag_name))