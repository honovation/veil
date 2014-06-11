from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


@composite_installer
def lxc_container_resource(container_name, user_name, mac_address, lan_interface, start_order, memory_limit=None, cpu_share=None):
    resources = [
        lxc_container_created_resource(container_name=container_name, user_name=user_name),
        file_resource(path='/var/lib/lxc/{}/config'.format(container_name), content=render_config('lxc-container.cfg.j2', name=container_name,
            mac_address=mac_address, lan_interface=lan_interface, start_order=start_order, memory_limit=memory_limit, cpu_share=cpu_share,
            DEPENDENCY_DIR=DEPENDENCY_DIR, DEPENDENCY_INSTALL_DIR=DEPENDENCY_INSTALL_DIR, PYPI_ARCHIVE_DIR=PYPI_ARCHIVE_DIR,
            is_precise=CURRENT_OS.codename == 'precise'), keep_origin=True)
    ]
    return resources


@atomic_installer
def lxc_container_created_resource(container_name, user_name):
    installed = os.path.exists('/var/lib/lxc/{}'.format(container_name))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(container_name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('create lxc container: %(container_name)s, and bind user %(user_name)s ...', {'container_name': container_name, 'user_name': user_name})
    shell_execute('lxc-create -t ubuntu -n {} -- -b {}'.format(container_name, user_name))
    if CURRENT_OS.codename == 'precise':
        shell_execute('ln -s /var/lib/lxc/{}/config /etc/lxc/auto/{}.conf'.format(container_name, container_name))


@composite_installer
def lxc_container_in_service_resource(container_name, restart_if_running=False):
    running = is_lxc_container_running(container_name)
    if running:
        action = 'RESTART' if restart_if_running else None
    else:
        action = 'START'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container_in_service?{}'.format(container_name)] = action or '-'
        return
    if not action:
        return
    if running:
        LOGGER.info('reboot lxc container: %(container_name)s ...', {'container_name': container_name})
        if CURRENT_OS.codename == 'precise':
            shell_execute('lxc-shutdown -n {} -r'.format(container_name), capture=True)
        else:
            shell_execute('lxc-stop -n {} -r'.format(container_name), capture=True)
    else:
        LOGGER.info('start lxc container: %(container_name)s ...', {'container_name': container_name})
        shell_execute('lxc-start -n {} -d'.format(container_name), capture=True)


def is_lxc_container_running(container_name):
    return 'RUNNING' in shell_execute('lxc-info -n {} -s'.format(container_name), capture=True)
