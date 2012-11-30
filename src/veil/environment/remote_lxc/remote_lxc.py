from __future__ import unicode_literals, print_function, division
import logging
import os
import fabric.api
from veil.frontend.cli import *
from veil.environment import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_lxc_payload.py')
LOGGER = logging.getLogger(__name__)

@script('provision-server')
def provision_server(provisioning_env, provisioning_server_name, user_name, user_password):
    provisioning_server = get_remote_veil_server(provisioning_env, provisioning_server_name)
    public_ssh_port = '{}22'.format(provisioning_server.ip.split('.')[0])
    fabric.api.env.host_string = '{}:{}'.format(provisioning_server.host.ssh_ip, provisioning_server.host.ssh_port)
    fabric.api.put(PAYLOAD, '/opt/remote_lxc_payload.py', use_sudo=True, mode=0700)
    fabric.api.sudo('python /opt/remote_lxc_payload.py {} {} {}'.format(
        '{}-{}'.format(provisioning_env, provisioning_server_name),
        provisioning_server.ip,
        public_ssh_port))

#def provision_iptables(ip):
#    output = fabric.api.sudo('iptables -L -n -t nat')
#    print('tcp dpt:{} to:{}:22'.format(public_ssh_port, ip))
#    if 'tcp dpt:{} to:{}:22'.format(public_ssh_port, ip) in output:
#        return
#    iptables_rule = '-A PREROUTING -p tcp --dport {} -j DNAT --to-destination {}:22'.format(public_ssh_port, ip)
#    LOGGER.warn('you should add following line to /etc/iptables.rule under *nat section,\nthen execute iptables-restore < /etc/iptables.rule:\n%(iptables_rule)s', {
#        'iptables_rule': iptables_rule
#    })
