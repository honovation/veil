from __future__ import unicode_literals, print_function, division
import os.path
import os
import logging
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@script('socks-proxy-up')
def bring_up_socks_proxy(target_env=None, gateway_host_name=None):
    target_env = target_env or os.getenv('VEIL_TUNNEL_TARGET_ENV')
    gateway_host_name = gateway_host_name or os.getenv('VEIL_TUNNEL_GATEWAY_HOST')
    hosts = list_veil_hosts(target_env)
    gateway_host = hosts[gateway_host_name] if gateway_host_name else hosts.values()[0]
    command = 'autossh -o StrictHostKeyChecking=no -D 1080 -p {} {}@{}'.format(
        gateway_host.ssh_port, gateway_host.ssh_user, gateway_host.external_ip)
    LOGGER.info('command: %(command)s', {'command': command})
    pass_control_to(command)


@script('redsocks-up')
def bring_up_redsocks():
    pass_control_to('redsocks -c {}/redsocks.conf'.format(os.path.dirname(__file__)))


@script('tunnel-up')
def bring_up_tunnel(target_env, gateway_host_name=None):
    hosts = list_veil_hosts(target_env)
    env = os.environ.copy()
    env['VEIL_TUNNEL_TARGET_ENV'] = target_env
    env['VEIL_TUNNEL_GATEWAY_HOST'] = gateway_host_name or ''
    try:
        for host in hosts.values():
            shell_execute('sudo iptables -t nat -I OUTPUT -p tcp -d {}.0/16 -j REDIRECT --to-ports 12345'.format(host.lan_range))
        shell_execute(
            'supervisord -c {}/tunnel-supervisord.cfg'.format(os.path.dirname(__file__)),
            env=env)
    finally:
        for host in hosts.values():
            shell_execute('sudo iptables -t nat -D OUTPUT -p tcp -d {}.0/16 -j REDIRECT --to-ports 12345'.format(host.lan_range))