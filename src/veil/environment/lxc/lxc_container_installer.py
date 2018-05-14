from __future__ import unicode_literals, print_function, division
import pylxd
from veil.frontend.cli import script
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


def get_lxc_client(verify_ssl=False):
    config = load_config_from(SECURITY_CONFIG_FILE, 'lxd_cert_path', 'lxd_endpoint', 'lxd_trust_password')
    cert_path = os.path.expanduser(config.lxd_cert_path)
    client = pylxd.Client(endpoint=config.lxd_endpoint, cert=('{}/lxd.crt'.format(cert_path), '{}/lxd.key'.format(cert_path)), verify=verify_ssl,
                          timeout=(3.05, 27))
    if not client.trusted:
        client.authenticate(config.lxd_trust_password)
    return client


@composite_installer
def lxc_container_resource(container_name, user_name, mac_address, lan_interface, start_order, etc_dir, log_dir,
                           editorial_dir=None, buckets_dir=None, data_dir=None, memory_limit=None, cpu_share=None,
                           cpus=None):
    container_path = as_path('/var/lib/lxc/') / container_name
    container_rootfs_path = container_path / 'rootfs'
    return [
        lxc_container_created_resource(container_name=container_name, user_name=user_name),
        file_resource(path=container_path / 'config',
                      content=render_config('lxc-container.cfg.j2', name=container_name,
                                            mac_address=mac_address, lan_interface=lan_interface,
                                            start_order=start_order, memory_limit=memory_limit, cpu_share=cpu_share,
                                            cpus=cpus, share_dir=SHARE_DIR, code_dir=VEIL_HOME.parent, etc_dir=etc_dir,
                                            editorial_dir=editorial_dir, buckets_dir=buckets_dir, data_dir=data_dir,
                                            log_dir=log_dir, user_name=user_name), keep_origin=True),
        file_resource(path=container_rootfs_path / 'etc' / 'sysctl.d' / '60-disable-ipv6.conf', content=render_config('disable-ipv6.conf'))
    ]


@atomic_installer
def lxc_container_created_resource(container_name, user_name, start_order, memory_limit=None, cpus=None, cpu_share=None):
    client = get_lxc_client()
    installed = client.containers.exists(container_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(container_name)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('create lxc container: %(container_name)s...', {'container_name': container_name})
    user_data = '''
    #cloud-config
    hostname: {container_name}
    users:
    - name: {user_name}
      gecos: {user_name}
      shell: /bin/bash
      sudo: ALL=(ALL) NOPASSWD:ALL
    '''.format(container_name=container_name, user_name=user_name)
    network_config = '''
    version: 2
    ethernets:
      eth0:
        addresses: [ 10.25.1.10/16 ]
        gateway4: 10.25.1.1
        nameservers: 
          addresses: [ 223.5.5.5, 223.6.6.6 ]
    '''
    container_config = {
        'name': container_name,
        'architecture': 'x86_64',
        'profiles': ['default'],
        'ephemeral': False,
        'config': {
            'boot.autostart': 'true',
            'boot.autostart.delay': '3',
            'boot.autostart.priority': start_order,
            'limits.cpu': cpus,
            'limits.cpu.allowance': cpu_share,
            'limits.memory': memory_limit,
            'user.user-data': user_data,
            'user.network-config': network_config
        },
        'devices': {
            'home': {
                'type': 'disk',
                'path': '/home/{}'.format(user_name),
                'source': '/home/{}'.format(user_name)
            }
        },
        'source': {
            'type': 'image',
            'alias': 'u1804'
        },
    }
    client.containers.create(container_config, wait=True)


@script('t')
def t():
    install_resource(lxc_container_created_resource(container_name='con-1', user_name='dejavu', start_order='1024'))


@atomic_installer
def lxc_container_in_service_resource(container_name, restart_if_running=False):
    client = get_lxc_client()
    running = client.containers.get(container_name).status_code == 103
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
        client.containers.get(container_name).restart()
    else:
        LOGGER.info('start lxc container: %(container_name)s ...', {'container_name': container_name})
        client.containers.get(container_name).start()
