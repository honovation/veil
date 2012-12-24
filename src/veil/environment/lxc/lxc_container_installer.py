from __future__ import unicode_literals, print_function, division
import os
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)

@composite_installer
def lxc_container_resource(container_name, mac_address, ip_address):
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR')
    if mirror:
        mirror = '{}:3142/mirrors.163.com/ubuntu'.format(mirror)
    else:
        mirror = 'http://mirrors.163.com/ubuntu'
    resources = [
        os_package_resource(name='lxc'),
        file_resource(path='/etc/default/lxc',
            content=render_config('lxc.cfg.j2', mirror=mirror)),
        lxc_container_created_resource(name=container_name),
        file_resource(path='/var/lib/lxc/{}/config'.format(container_name), content=render_config(
                'lxc-container.cfg.j2', name=container_name,
                mac_address=mac_address, ip_address=ip_address))
    ]
    return resources


@atomic_installer
def lxc_container_created_resource(name):
    is_installed = os.path.exists('/var/lib/lxc/{}'.format(name))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(name)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    LOGGER.info('create lxc container: %(name)s ...', {'name': name})
    shell_execute('lxc-create -t ubuntu -n {}'.format(name))


@atomic_installer
def lxc_container_in_service_resource(name):
    is_running = False if 'STOPPED' in shell_execute('lxc-info -n {}'.format(name), capture=True) else True
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container_in_service?{}'.format(name)] = '-' if is_running else 'START'
        return
    if is_running:
        return
    LOGGER.info('start lxc container: %(name)s ...', {'name': name})
    shell_execute('lxc-start -n {} -d'.format(name), capture=True)
