from __future__ import unicode_literals, print_function, division
import platform
import pwd
from veil.environment.lxd import *
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


def get_idmap():
    current_user_pwd_entry = pwd.getpwnam(CURRENT_USER)
    return current_user_pwd_entry.pw_uid, current_user_pwd_entry.pw_gid


def generate_lxc_container_user_data(container_name, hostname, timezone, user_name):
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
      - sed -i -e '{no_password_authentication}' /etc/ssh/sshd_config
      - sed -i -e '{no_root_login}' /etc/ssh/sshd_config
      - systemctl restart ssh
    '''.format(container_name=container_name, hostname=hostname, timezone=timezone, user_name=user_name,
               no_password_authentication='/^PasswordAuthentication\s/{h;s/\s.*/ no/};${x;/^$/{s//PasswordAuthentication no/;H};x}',
               no_root_login='/^PermitRootLogin\s/{h;s/\s.*/ no/};${x;/^$/{s//PermitRootLogin no/;H};x}')
    return user_data


def generate_lxc_container_network_config(ip_address, gateway, name_servers):
    network_config = '''
    version: 2
    ethernets:
      eth0:
        addresses: [ {ip_address}/16 ]
        gateway4: {gateway}
        nameservers:
          addresses: [ {name_servers} ]
    '''.format(ip_address=ip_address, gateway=gateway, name_servers=name_servers)
    return network_config


def generate_lxc_container_general_config(user_data, network_config, start_order, memory_limit=None, cpus=None, cpu_share=None, idmap=None):
    idmap = idmap or get_idmap()
    config_part = {
        'boot.autostart': 'true',
        'boot.autostart.delay': '3',
        'boot.autostart.priority': start_order,
        'user.user-data': user_data,
        'user.network-config': network_config,
        'raw.idmap': 'uid {host_uid} 1000\ngid {host_gid} 1000'.format(host_uid=idmap[0], host_gid=idmap[1])
    }
    if cpus:
        config_part['limits.cpu'] = cpus
    if cpu_share:
        if not str(cpu_share).endswith('%'):
            cpu_share = '{}%'.format(cpu_share)
        config_part['limits.cpu.allowance'] = cpu_share
    if memory_limit:
        if not memory_limit.endswith('B'):
            memory_limit = '{}B'.format(memory_limit)
        config_part['limits.memory'] = memory_limit
    return config_part


def generate_lxc_container_devices_config(user_name, etc_dir, log_dir, var_dir=None, editorial_dir=None, buckets_dir=None, data_dir=None, barman_dir=None):
    devices_config = {
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
    }

    if var_dir:
        devices_config['var'] = {
            'type': 'disk',
            'path': var_dir,
            'source': var_dir
        }
    if editorial_dir:
        devices_config['editorial'] = {
            'type': 'disk',
            'path': editorial_dir,
            'source': editorial_dir
        }
    if buckets_dir:
        devices_config['buckets'] = {
            'type': 'disk',
            'path': buckets_dir,
            'source': buckets_dir
        }
    if data_dir:
        devices_config['data'] = {
            'type': 'disk',
            'path': data_dir,
            'source': data_dir
        }
    if barman_dir:
        devices_config['data'] = {
            'type': 'disk',
            'path': barman_dir,
            'source': barman_dir
        }
    return devices_config


@atomic_installer
def lxc_container_resource(container_name, hostname, timezone, user_name, ip_address, gateway, name_servers, start_order, etc_dir, log_dir, var_dir=None,
                           editorial_dir=None, buckets_dir=None, data_dir=None, barman_dir=None, memory_limit=None, cpus=None, cpu_share=None, idmap=None):
    client = LXDClient(local=True)
    installed = client.is_container_exists(container_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(container_name)] = '-' if installed else 'INSTALL'
        return
    user_data = generate_lxc_container_user_data(container_name, hostname, timezone, user_name)
    network_config = generate_lxc_container_network_config(ip_address, gateway, name_servers)
    general_config = generate_lxc_container_general_config(user_data, network_config, start_order, memory_limit=memory_limit, cpus=cpus, cpu_share=cpu_share,
                                                           idmap=idmap)
    devices_config = generate_lxc_container_devices_config(user_name, etc_dir, log_dir, var_dir=var_dir, editorial_dir=editorial_dir, buckets_dir=buckets_dir,
                                                           data_dir=data_dir, barman_dir=barman_dir)
    if installed:
        container = client.get_container(container_name)
        if container.config['user.user-data'] != user_data:
            LOGGER.info('Delete container as user-data changed: %(container_name)s, %(old)s, %(new)s', {
                'container_name': container_name,
                'old': container.config['user.user-data'],
                'new': user_data
            })
            container.stop()
            container.delte()
            installed = False
        elif container.config['user.network-config'] != network_config:
            LOGGER.info('Delete container as network-config changed: %(container_name)s, %(old)s, %(new)s', {
                'container_name': container_name,
                'old': container.config['user.network-config'],
                'new': network_config
            })
            container.stop()
            container.delte()
            installed = False

    if installed:
        container = client.get_container(container_name)
        LOGGER.info('Update lxc container: %(container_name)s', {'container_name': container_name})
        if container.profiles[0] != LXD_PROFILE_NAME:
            new_profiles = [LXD_PROFILE_NAME]
            LOGGER.info('change container profile: %(old_profiles)s, %(new_profiles)s', {
                'old_profiles': container.profiles,
                'new_profiles': new_profiles
            })
            container.profiles = new_profiles
        container.config = general_config
        container.devices = devices_config
        container.save(wait=True)
        return

    LOGGER.info('Create lxc container: %(container_name)s...', {'container_name': container_name})
    container_config = DictObject({
        'name': container_name,
        'architecture': 'x86_64',
        'profiles': [LXD_PROFILE_NAME],
        'ephemeral': False,
        'config': general_config,
        'devices': devices_config,
        'source': {
            'type': 'image',
            'alias': platform.linux_distribution()[2]
        },
    })
    client.create_container(container_config, wait=True)


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
