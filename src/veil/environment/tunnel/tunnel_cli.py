from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.model.collection import *
from veil.model.event import *
from veil.utility.shell import *
from veil.server.process import *

LOGGER = logging.getLogger(__name__)
host_lan_ranges = set()


@script('socks-proxy-up')
def bring_up_socks_proxy(target_env=None, gateway_host_name=None, gateway_host_ssh_port=None, gateway_host_ssh_user=None):
    target_env = target_env or os.getenv('VEIL_TUNNEL_TARGET_ENV')
    gateway_host_name = gateway_host_name or os.getenv('VEIL_TUNNEL_GATEWAY_HOST_NAME')
    gateway_host_ssh_port = gateway_host_ssh_port or os.getenv('VEIL_TUNNEL_GATEWAY_HOST_SSH_PORT')
    gateway_host_ssh_user = gateway_host_ssh_user or os.getenv('VEIL_TUNNEL_GATEWAY_HOST_SSH_USER')
    hosts = list_veil_hosts(target_env)
    if gateway_host_name:
        gateway_host = hosts.get(
            gateway_host_name,
            DictObject(external_ip=gateway_host_name, ssh_port=gateway_host_ssh_port, ssh_user=gateway_host_ssh_user)
        )
    else:
        gateway_host = hosts.values()[0]
    command = 'autossh -o StrictHostKeyChecking=no -D 0.0.0.0:1080 -p {} {}@{}'.format(
        gateway_host.ssh_port, gateway_host.ssh_user, gateway_host.external_ip)
    LOGGER.info('command: %(command)s', {'command': command})
    pass_control_to(command)


@script('redsocks-up')
def bring_up_redsocks():
    pass_control_to('redsocks -c {}/redsocks.conf'.format(os.path.dirname(__file__)))


@script('tunnel-up')
def bring_up_tunnel(target_env, gateway_host_name=None, gateway_host_ssh_port=None, gateway_host_ssh_user=None):
    env = os.environ.copy()
    env['VEIL_TUNNEL_TARGET_ENV'] = target_env
    env['VEIL_TUNNEL_GATEWAY_HOST_NAME'] = gateway_host_name or ''
    env['VEIL_TUNNEL_GATEWAY_HOST_SSH_PORT'] = gateway_host_ssh_port or '22'
    env['VEIL_TUNNEL_GATEWAY_HOST_SSH_USER'] = gateway_host_ssh_user or 'dejavu'

    hosts = list_veil_hosts(target_env)
    set_host_lan_ranges(hosts)
    add_iptables_rules()
    shell_execute('supervisord -c {}/tunnel-supervisord.cfg'.format(os.path.dirname(__file__)), env=env)


def set_host_lan_ranges(hosts):
    global host_lan_ranges
    host_lan_ranges = {host.lan_range for host in hosts.values()}


def add_iptables_rules():
    for lan_range in host_lan_ranges:
        shell_execute('sudo iptables -t nat -I OUTPUT -p tcp -d {}.0/24 -j REDIRECT --to-ports 12345'.format(lan_range))


@event(EVENT_PROCESS_TEARDOWN)
def remove_iptables_rules():
    for lan_range in host_lan_ranges:
        try:
            shell_execute('sudo iptables -t nat -D OUTPUT -p tcp -d {}.0/24 -j REDIRECT --to-ports 12345'.format(lan_range))
        except:
            LOGGER.exception('Cannot remove iptables rules for lan range: %(lan_range)s', {'lan_range': lan_range})
