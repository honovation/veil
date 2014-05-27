from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


@composite_installer
def lxc_container_resource(container_name, mac_address, lan_interface, memory_limit=None, cpu_share=None):
    resources = [
        os_package_resource(name='lxc'),
        file_resource(path='/etc/default/lxc-net', content=render_config('lxc-net.j2')) if VEIL_OS.codename == 'trusty' else file_resource(
            path='/etc/default/lxc', content=render_config('lxc.cfg.j2', mirror=VEIL_APT_URL)),
        file_resource(path='/etc/sysctl.d/60-lxc-ipv4-ip-forward.conf', content='net.ipv4.ip_forward=1',
            cmd_run_after_installed='sysctl -p /etc/sysctl.d/60-lxc-ipv4-ip-forward.conf'),
        lxc_container_created_resource(name=container_name),
        file_resource(path='/var/lib/lxc/{}/rootfs/etc/apt/sources.list'.format(container_name),
            content=render_config('sources.list.j2', codename=VEIL_OS.codename, mirror=VEIL_APT_URL)),
        file_resource(path='/var/lib/lxc/{}/config'.format(container_name), content=render_config('lxc-container.cfg.j2', name=container_name,
            mac_address=mac_address, lan_interface=lan_interface, memory_limit=memory_limit, cpu_share=cpu_share,
            is_trusty=VEIL_OS.codename == 'trusty'))
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
    if VEIL_OS.codename == 'precise':
        shell_execute('ln -s /var/lib/lxc/{}/config /etc/lxc/auto/{}.conf'.format(name, name))


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
