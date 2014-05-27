from __future__ import unicode_literals, print_function, division
import logging
from veil_component import as_path
from veil.utility.shell import *
from veil_installer import *
from veil.server.config import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def lxc_container_network_resource(container_name, ip_address, gateway):
    container_rootfs_path = as_path('/var/lib/lxc/') / container_name / 'rootfs'
    network_interfaces_path = container_rootfs_path / 'etc' / 'network' / 'interfaces'
    config_content = render_config('interfaces.j2', ip_address=ip_address, gateway=gateway)
    is_installed = config_content == network_interfaces_path.text()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_network?container_name={}&ip_address={}'.find(container_name, ip_address)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    LOGGER.info('set container network: in %(container_name)s to %(ip_address)s via %(gateway)s', {
        'container_name': container_name,
        'ip_address': ip_address,
        'gateway': gateway
    })
    network_interfaces_path.write_text(config_content)


@atomic_installer
def lxc_container_name_servers_resource(container_name, name_servers):
    container_rootfs_path = as_path('/var/lib/lxc/') / container_name / 'rootfs'
    resolve_conf_path = container_rootfs_path / 'etc' / 'resolvconf' / 'resolv.conf.d' / 'tail'
    config_content = '\n'.join('nameserver {}'.format(name_server) for name_server in name_servers.split(','))
    is_installed = config_content == resolve_conf_path.text()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_name servers_resource?container_name={}&name_servers={}'.find(container_name, name_servers)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    LOGGER.info('set container name servers: in %(container_name)s to %(name_servers)s', {'container_name': container_name, 'name_servers': name_servers})
    resolve_conf_path.write_text(config_content)
    shell_execute('resolvconf -u')