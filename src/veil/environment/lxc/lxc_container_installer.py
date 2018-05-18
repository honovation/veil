from __future__ import unicode_literals, print_function, division
import pwd
from veil.environment.lxd import *
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


def get_idmap():
    current_user_pwd_entry = pwd.getpwnam(CURRENT_USER)
    return current_user_pwd_entry.pw_uid, current_user_pwd_entry.pw_gid


@atomic_installer
def lxc_container_resource(container_name, hostname, timezone, user_name, ip_address, gateway, name_servers, start_order, memory_limit=None, cpus=None,
                           cpu_share=None, idmap=None, etc_dir=None, log_dir=None, editorial_dir=None, buckets_dir=None, data_dir=None):
    client = LXDClient(local=True).client
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
    hostname: {hostname}
    timezone: {timezone}
    users:
    - name: {user_name}
      gecos: {user_name}
      shell: /bin/bash
      sudo: ALL=(ALL) NOPASSWD:ALL
    write_files:
      - path: /etc/sysctl.d/10-disable-ipv6.conf
        permissions: 0644
        owner: root
        content: |
          net.ipv6.conf.all.disable_ipv6 = 1
          net.ipv6.conf.default.disable_ipv6 = 1
          net.ipv6.conf.lo.disable_ipv6 = 1
    runcmd:
      - systemctl restart systemd-sysctl.service
      - sed -i -e '/^PermitRootLogin/s/^.*$/PermitRootLogin no/' /etc/ssh/sshd_config
      - sed -i -e '/^UseDNS/s/^.*$/UseDNS no/' /etc/ssh/sshd_config
      - sed -i -e '/^PasswordAuthentication/s/^.*$/PasswordAuthentication no/' /etc/ssh/sshd_config
      - systemctl restart ssh
    '''.format(container_name=container_name, hostname=hostname, timezone=timezone, user_name=user_name)
    network_config = '''
    version: 2
    ethernets:
      eth0:
        addresses: [ {ip_address}/16 ]
        gateway4: {gateway}
        nameservers: 
          addresses: [ {name_servers} ]
    '''.format(ip_address=ip_address, gateway=gateway, name_servers=name_servers)
    idmap = idmap or get_idmap()
    container_config = DictObject({
        'name': container_name,
        'architecture': 'x86_64',
        'profiles': ['default'],
        'ephemeral': False,
        'config': {
            'boot.autostart': 'true',
            'boot.autostart.delay': '3',
            'boot.autostart.priority': start_order,
            'user.user-data': user_data,
            'user.network-config': network_config,
            'raw.idmap': 'uid {host_uid} 1000\ngid {host_gid} 1000'.format(host_uid=idmap[0], host_gid=idmap[1])
        },
        'devices': {
            'home': {
                'type': 'disk',
                'path': '/home/{}'.format(user_name),
                'source': '/home/{}'.format(user_name)
            },
            'share': {
                'type': 'disk',
                'path': SHARE_DIR,
                'source': SHARE_DIR
            },
            'code': {
                'type': 'disk',
                'path': VEIL_HOME.parent,
                'source': VEIL_HOME.parent
            },
            'etc': {
                'type': 'disk',
                'path': etc_dir,
                'source': etc_dir
            },
            'log': {
                'type': 'disk',
                'path': log_dir,
                'source': log_dir
            }
        },
        'source': {
            'type': 'image',
            'alias': 'u1804'
        },
    })
    if cpus:
        container_config.config['limits.cpu'] = cpus
    if cpu_share:
        container_config.config['limits.cpu.allowance'] = cpu_share
    if memory_limit:
        if not memory_limit.endswith('B'):
            memory_limit = '{}B'.format(memory_limit)
        container_config.config['limits.memory'] = memory_limit

    if editorial_dir:
        container_config.devices['editorial'] = {
            'type': 'disk',
            'path': editorial_dir,
            'source': editorial_dir
        }
    if buckets_dir:
        container_config.devices['buckets'] = {
            'type': 'disk',
            'path': buckets_dir,
            'source': buckets_dir
        }
    if data_dir:
        container_config.devices['data'] = {
            'type': 'disk',
            'path': data_dir,
            'source': data_dir
        }
    client.containers.create(container_config, wait=True)


@atomic_installer
def lxc_container_in_service_resource(container_name, restart_if_running=False):
    container = LXDClient(local=True).get_container(container_name)
    running = container.status_code == 103
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
        container.restart()
    else:
        LOGGER.info('start lxc container: %(container_name)s ...', {'container_name': container_name})
        container.start()
