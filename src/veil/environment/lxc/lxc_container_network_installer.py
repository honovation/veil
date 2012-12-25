from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.path import *
from veil.server.config import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def lxc_container_network_resource(container_name, ip_address, gateway):
    CONTAINER_ROOTFS_PATH = as_path('/var/lib/lxc/') / container_name / 'rootfs'
    NETWORK_INTERFACES_PATH = CONTAINER_ROOTFS_PATH / 'etc' / 'network' / 'interfaces'
    config_content = render_config('interfaces.j2', ip_address=ip_address, gateway=gateway)
    is_installed = config_content == NETWORK_INTERFACES_PATH.text()
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
    NETWORK_INTERFACES_PATH.write_text(config_content)
