from __future__ import unicode_literals, print_function, division
import pwd
import grp
import platform
from veil.environment.lxd import *
from veil.profile.installer import *
from veil.utility.clock import *

LOGGER = logging.getLogger(__name__)


def make_user_data(hostname, timezone, user_name):
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
    '''.format(hostname=hostname, timezone=timezone, user_name=user_name,
               no_password_authentication='/^PasswordAuthentication\s/{h;s/\s.*/ no/};${x;/^$/{s//PasswordAuthentication no/;H};x}',
               no_root_login='/^PermitRootLogin\s/{h;s/\s.*/ no/};${x;/^$/{s//PermitRootLogin no/;H};x}')
    return user_data


def make_network_config(ip_address, gateway, name_servers):
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


def make_general_config(user_data, network_config, start_order, memory_limit=None, cpus=None, cpu_share=None):
    host_uid = pwd.getpwnam(CURRENT_USER).pw_uid
    host_gid = grp.getgrnam(CURRENT_USER_GROUP).gr_gid
    config_part = {
        'boot.autostart': 'true',
        'boot.autostart.delay': '3',
        'boot.autostart.priority': start_order,
        'user.user-data': user_data,
        'user.network-config': network_config,
        'raw.idmap': 'uid {host_uid} 1000\ngid {host_gid} 1000'.format(host_uid=host_uid, host_gid=host_gid)
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


def make_devices_config(user_name, etc_dir, log_dir, var_dir=None, editorial_dir=None, buckets_dir=None, data_dir=None, barman_dir=None):
    assert not var_dir or not editorial_dir and not buckets_dir and not data_dir and not barman_dir
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
        devices_config['barman'] = {
            'type': 'disk',
            'path': barman_dir,
            'source': barman_dir
        }
    return devices_config


@atomic_installer
def lxc_container_resource(container_name, hostname, timezone, user_name, ip_address, gateway, name_servers, start_order, etc_dir, log_dir, var_dir=None,
                           editorial_dir=None, buckets_dir=None, data_dir=None, barman_dir=None, memory_limit=None, cpus=None, cpu_share=None):
    client = LXDClient(local=True)
    installed = client.is_container_exists(container_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container?{}'.format(container_name)] = '-' if installed else 'INSTALL'
        return
    user_data = make_user_data(hostname, timezone, user_name)
    network_config = make_network_config(ip_address, gateway, name_servers)
    general_config = make_general_config(user_data, network_config, start_order, memory_limit=memory_limit, cpus=cpus, cpu_share=cpu_share)
    devices_config = make_devices_config(user_name, etc_dir, log_dir, var_dir=var_dir, editorial_dir=editorial_dir, buckets_dir=buckets_dir,
                                         data_dir=data_dir, barman_dir=barman_dir)
    if installed:
        need_delete_container = False
        container = client.get_container(container_name)
        if container.config['user.user-data'] != user_data:
            LOGGER.info('Delete container as user-data changed: %(container_name)s, %(old)s, %(new)s', {
                'container_name': container_name,
                'old': container.config['user.user-data'],
                'new': user_data
            })
            need_delete_container = True
        if container.config['user.network-config'] != network_config:
            LOGGER.info('Delete container as network-config changed: %(container_name)s, %(old)s, %(new)s', {
                'container_name': container_name,
                'old': container.config['user.network-config'],
                'new': network_config
            })
            need_delete_container = True
        if need_delete_container:
            if container.running:
                container.stop(wait=True)
            container.rename('{}-deleted-at-{}'.format(container.name, get_current_timestamp()), wait=True)
            installed = False

    if installed:
        container = client.get_container(container_name)
        LOGGER.info('Update lxc container: %(container_name)s, %(general_config)s, %(devices_config)s', {
            'container_name': container_name,
            'general_config': general_config,
            'devices_config': devices_config
        })
        container.config.update(general_config)
        container.devices = devices_config
        container.save(wait=True)
        return

    LOGGER.info('Create lxc container: %(container_name)s, %(general_config)s, %(devices_config)s...', {
        'container_name': container_name,
        'general_config': general_config,
        'devices_config': devices_config
    })
    container_config = DictObject({
        'name': container_name,
        'architecture': platform.machine(),
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
    if container.running:
        action = 'RESTART' if restart_if_running else None
    else:
        action = 'START'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['lxc_container_in_service?{}'.format(container_name)] = action or '-'
        return
    if not action:
        return
    if container.running:
        LOGGER.info('reboot lxc container: %(container_name)s ...', {'container_name': container_name})
        container.restart(wait=True)
    else:
        LOGGER.info('start lxc container: %(container_name)s ...', {'container_name': container_name})
        container.start(wait=True)
