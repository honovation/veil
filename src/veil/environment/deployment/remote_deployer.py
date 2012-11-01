from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import fabric.api
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.backend.shell import *
from veil.utility.clock import get_current_timestamp

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_deployer_payload.py')

@script('deploy-env')
def deploy_env(deploying_env):
    tag_before_real_deploy()
    for veil_server_name in get_veil_servers(deploying_env).keys():
        deploy_server('{}/{}'.format(deploying_env, veil_server_name))


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

def tag_before_real_deploy():
    shell_execute('git tag -a deploy_{}'.format(get_current_timestamp()))