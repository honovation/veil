from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


@composite_installer
def lxc_container_resource(container_name, user_name, mac_address, lan_interface, start_order, etc_dir, log_dir,
                           editorial_dir=None, buckets_dir=None, data_dir=None, memory_limit=None, cpu_share=None,
                           cpus=None):
    container_path = as_path('/var/lib/lxc/') / container_name
    container_rootfs_path = container_path / 'rootfs'
    utsname = container_name.replace('@', '')
    return [
        lxc_container_created_resource(container_name=container_name, user_name=user_name),
        file_resource(path=container_path / 'config',
                      content=render_config('lxc-container.cfg.j2', utsname=utsname, name=container_name,
                                            mac_address=mac_address, lan_interface=lan_interface,
                                            start_order=start_order, memory_limit=memory_limit, cpu_share=cpu_share,
                                            cpus=cpus, share_dir=SHARE_DIR, code_dir=VEIL_HOME.parent, etc_dir=etc_dir,
                                            editorial_dir=editorial_dir, buckets_dir=buckets_dir, data_dir=data_dir,
                                            log_dir=log_dir, user_name=user_name), keep_origin=True),
        file_resource(path=container_rootfs_path / 'etc/sysctl.d/60-disable-ipv6.conf',
                      content=render_config('disable-ipv6.conf'), cmd_run_after_updated='sysctl --system'),
        file_resource(path=container_rootfs_path / 'etc' / 'hostname', content=utsname,
                      cmd_run_after_updated='hostname {}'.format(utsname)),
        file_resource(path=container_rootfs_path / 'etc' / 'hosts', content=render_config('hosts', utsname=utsname))
    ]


@atomic_installer
def lxc_container_created_resource(container_name, user_name):
    installed = os.path.exists('/var/lib/lxc/{}'.format(container_name))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(container_name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('create lxc container: %(container_name)s, and bind user %(user_name)s ...', {
        'container_name': container_name, 'user_name': user_name
    })
    shell_execute('lxc-create -t ubuntu -n {} -- -b {}'.format(container_name, user_name))


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
        shell_execute('lxc-stop -n {} -r'.format(container_name), capture=True)
    else:
        LOGGER.info('start lxc container: %(container_name)s ...', {'container_name': container_name})
        shell_execute('lxc-start -n {} -d'.format(container_name), capture=True)


def is_lxc_container_running(container_name):
    return 'RUNNING' in shell_execute('lxc-info -n {} -s'.format(container_name), capture=True)
