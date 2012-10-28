from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import fabric.api
import os.path
from veil.frontend.cli import *
from veil.environment import *

DEPLOY_PY = os.path.join(os.path.dirname(__file__), 'deploy.py')

@script('deploy-env')
def deploy_env(argv):
    pass


@script('deploy-server')
def deploy_server(*argv):
    argument_parser = ArgumentParser('Deploy a remote server')
    argument_parser.add_argument('remote_veil_server', type=str,
        help='remote VEIL_SERVER, of format VEIL_ENV/VEIL_SERVER_NAME')
    argument_parser.add_argument('--deployed-via', help='override how to access the server to deploy')
    args = argument_parser.parse_args(argv)
    veil_server = get_remote_veil_server(args.remote_veil_server)
    deployed_via = args.deployed_via or veil_server.deployed_via
    fabric.api.env.host_string = deployed_via
    fabric.api.put(DEPLOY_PY, '/opt/deploy.py', use_sudo=True, mode=0700)
    fabric.api.sudo('python /opt/deploy.py {} {} {} {}'.format(
        get_application_codebase(),
        '/opt/{}'.format(get_application_name()),
        *split_veil_server_code(args.remote_veil_server)))