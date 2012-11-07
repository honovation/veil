from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
from fabric.colors import green
from veil.frontend.cli import *
from veil.environment import *
from veil.backend.shell import *
import os
import datetime
import fabric.api

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_deployer_payload.py')

@script('deploy-env')
def deploy_env(deploying_env):
    for veil_server_name in sorted(get_veil_servers(deploying_env).keys()):
        deploy_server('{}/{}'.format(deploying_env, veil_server_name))
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
    print(green('switch to env-{} branch...'.format(veil_server_env)))
    shell_execute('git checkout env-{}'.format(veil_server_env), cwd=VEIL_HOME)
    print(green('merge master to this...'))
    shell_execute('git merge master', cwd=VEIL_HOME)
    print(green('push env-{} to github...'.format(veil_server_env)))
    shell_execute('git push origin env-{}'.format(veil_server_env), cwd=VEIL_HOME)
    print(green('switch back to master...'))
    shell_execute('git checkout master', cwd=VEIL_HOME)
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

def tag_deploy(deploying_env):
    shell_execute('git tag deploy-{}-{}'.format(deploying_env, datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')))
    shell_execute('git push --tags')