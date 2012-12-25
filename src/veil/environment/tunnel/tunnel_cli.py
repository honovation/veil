from __future__ import unicode_literals, print_function, division
import os.path
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *

@script('socks-proxy-up')
def bring_up_socks_proxy(target_env=None, gateway_host_name=None):
    target_env = target_env or os.getenv('VEIL_TUNNEL_TARGET_ENV')
    gateway_host_name = gateway_host_name or os.getenv('VEIL_TUNNEL_GATEWAY_HOST')
    hosts = list_veil_hosts(target_env)
    gateway_host = hosts[gateway_host_name] if gateway_host_name else hosts.values()[0]
    pass_control_to('autossh -o StrictHostKeyChecking=no -D 1080 -p {} {}@{}'.format(
        gateway_host.ssh_port, gateway_host.ssh_user, gateway_host.ssh_ip))


@script('redsocks-up')
def bring_up_redsocks():
    pass_control_to('redsocks -c {}/redsocks.conf'.format(os.path.dirname(__file__)))


@script('tunnel-up')
def bring_up_tunnel(target_env, gateway_host_name=None):
    env = os.environ.copy()
    env['VEIL_TUNNEL_TARGET_ENV'] = target_env
    env['VEIL_TUNNEL_GATEWAY_HOST'] = gateway_host_name or ''
    try:
        shell_execute('sudo iptables -t nat -I OUTPUT -p tcp -d 10.24.0.0/16 -j REDIRECT --to-ports 12345')
        shell_execute(
            'supervisord -c {}/tunnel-supervisord.cfg'.format(os.path.dirname(__file__)),
            env=env)
    finally:
        shell_execute('sudo iptables -t nat -D OUTPUT -p tcp -d 10.24.0.0/16 -j REDIRECT --to-ports 12345')