from __future__ import unicode_literals, print_function, division
import logging
import os
import fabric.api
from veil.utility.path import *
from veil.frontend.cli import *
from veil.environment import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_lxc_payload.py')
LOGGER = logging.getLogger(__name__)

@script('provision-env')
def provision_env(provisioning_env, config_dir):
    for provisioning_server_name in get_veil_servers(provisioning_env).keys():
        provision_server(provisioning_env, provisioning_server_name, config_dir)


@script('provision-server')
def provision_server(provisioning_env, provisioning_server_name, config_dir):
    provisioning_server = get_remote_veil_server(provisioning_env, provisioning_server_name)
    sequence_no = provisioning_server.ip.split('.')[-1]
    server_config_dir = as_path('{}/env/{}/{}'.format(config_dir, provisioning_env, provisioning_server_name))
    with open('{}/pass'.format(server_config_dir)) as f:
        user_name, user_password = f.read().split(':')
        user_password = user_password.strip()
    fabric.api.env.host_string = '{}:{}'.format(provisioning_server.host.ssh_ip, provisioning_server.host.ssh_port)
    with open('{}/host/{}/pass'.format(config_dir, provisioning_server.host.name)) as f:
        host_user_name, host_user_password = f.read().split(':')
        host_user_password = host_user_password.strip()
    fabric.api.env.host_string = '{}@{}'.format(host_user_name, fabric.api.env.host_string)
    fabric.api.env.passwords[fabric.api.env.host_string] = host_user_password
    fabric.api.put(PAYLOAD, '/opt/remote_lxc_payload.py', use_sudo=True, mode=0600)
    fabric.api.sudo('python /opt/remote_lxc_payload.py {} {} {} {}'.format(
        '{}-{}'.format(provisioning_env, provisioning_server_name),
        sequence_no, user_name, user_password))
    fabric.api.env.host_string = '{}@{}:{}22'.format(user_name, provisioning_server.host.ssh_ip, sequence_no)
    fabric.api.env.passwords[fabric.api.env.host_string] = user_password
    fabric.api.put(
        server_config_dir / 'known_hosts', '/home/{}/.ssh/known_hosts'.format(user_name),
        use_sudo=True, mode=0644)
    if (server_config_dir / 'config').exists():
        for f in (server_config_dir / 'config').listdir():
            fabric.api.put(f, '~', mode=0600)
    fabric.api.put(
        server_config_dir / 'known_hosts', '/root/.ssh/known_hosts',
        use_sudo=True, mode=0644)

