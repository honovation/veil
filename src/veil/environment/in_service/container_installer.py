from __future__ import unicode_literals, print_function, division
import os
import fabric.api
import tempfile
from veil_component import as_path
from veil_installer import *
from veil.environment import *
from veil.server.config import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'container_installer_payload.py')
veil_hosts_with_payload_uploaded = []

@composite_installer
def veil_env_containers_resource(veil_env_name, config_dir):
    resources = []
    for veil_server_name in list_veil_server_names(veil_env_name):
        resources.append(veil_server_container_resource(veil_env_name=veil_env_name, veil_server_name=veil_server_name))
        resources.append(veil_server_container_config_resource(veil_env_name=veil_env_name, veil_server_name=veil_server_name, config_dir=config_dir))
    return resources


@atomic_installer
def veil_server_container_resource(veil_env_name, veil_server_name):
    server = get_veil_server(veil_env_name, veil_server_name)
    host = get_veil_host(veil_env_name, server.host_name)
    fabric.api.env.host_string = '{}@{}:{}'.format(host.ssh_user, host.internal_ip, host.ssh_port)
    fabric.api.env.forward_agent = True
    installer_file_content = render_installer_file(veil_env_name, veil_server_name)
    installer_file_path = '/opt/INSTALLER-{}-{}'.format(veil_env_name, veil_server_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container?{}-{}'.format(veil_env_name, veil_server_name)
        dry_run_result[key] = 'INSTALL'
        return
    remote_put_content(installer_file_path, installer_file_content, use_sudo=True, mode=0600)
    if fabric.api.env.host_string not in veil_hosts_with_payload_uploaded:
        fabric.api.put(PAYLOAD, '/opt/container_installer_payload.py', use_sudo=True, mode=0600)
        veil_hosts_with_payload_uploaded.append(fabric.api.env.host_string)
    fabric.api.sudo('python /opt/container_installer_payload.py {} {}'.format(VEIL_FRAMEWORK_CODEBASE, installer_file_path))


@composite_installer
def veil_server_container_config_resource(veil_env_name, veil_server_name, config_dir):
    server = get_veil_server(veil_env_name, veil_server_name)
    host = get_veil_host(veil_env_name, server.host_name)
    veil_server_user_name = host.ssh_user
    env_config_dir = config_dir / '{}'.format(veil_env_name)
    server_config_dir = env_config_dir / 'servers/{}'.format(veil_server_name)
    resources = [
        veil_server_container_file_resource(
            local_path=config_dir / 'share' / 'iptablesload',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/etc/network/if-pre-up.d/iptablesload',
            owner='root', owner_group='root', mode=0755),
        veil_server_container_file_resource(
            local_path=config_dir / 'share' / 'iptablessave',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/etc/network/if-post-down.d/iptablessave',
            owner='root', owner_group='root', mode=0755),
        veil_server_container_file_resource(
            local_path=config_dir / 'share' / 'sudoers.d.ssh-auth-sock',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/etc/sudoers.d/ssh-auth-sock',
            owner='root', owner_group='root', mode=0440),
        veil_server_container_file_resource(
            local_path=config_dir / 'share' / 'sudoers.d.no-password',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/etc/sudoers.d/no-password',
            owner='root', owner_group='root', mode=0440),
        veil_server_container_directory_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0755),
        veil_server_container_file_resource(
            local_path=env_config_dir / '.ssh' / 'authorized_keys',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh/authorized_keys'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644),
        veil_server_container_file_resource(
            local_path=env_config_dir / '.ssh' / 'known_hosts',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh/known_hosts'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644),
        veil_server_container_directory_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/root/.ssh',
            owner='root', owner_group='root', mode=0755),
        veil_server_container_file_resource(
            local_path=env_config_dir / '.ssh' / 'known_hosts',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/root/.ssh/known_hosts',
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644)]
    if (env_config_dir / '.config').exists():
        resources.append(veil_server_container_file_resource(
            local_path=env_config_dir / '.config',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path=('/home/{}/.config'.format(veil_server_user_name)),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0600))
    for local_path in server_config_dir.files():
        if local_path.name != 'README':
            resources.append(veil_server_container_file_resource(
                local_path=local_path,
                veil_env_name=veil_env_name, veil_server_name=veil_server_name,
                remote_path=('/home/{}/{}'.format(veil_server_user_name, local_path.name)),
                owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0600))
    if (server_config_dir / '.ssh' / 'id_rsa').exists():
        resources.append(veil_server_container_file_resource(
            local_path=server_config_dir / '.ssh' / 'id_rsa',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh/id_rsa'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0600))
        resources.append(veil_server_container_file_resource(
            local_path=server_config_dir / '.ssh' / 'id_rsa',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/root/.ssh/id_rsa',
            owner='root', owner_group='root', mode=0600))
    return resources


@atomic_installer
def veil_server_container_directory_resource(veil_env_name, veil_server_name, remote_path, owner, owner_group, mode):
    container_rootfs_path = '/var/lib/lxc/{}-{}/rootfs'.format(veil_env_name, veil_server_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container_directory?{}-{}&path={}'.format(veil_env_name, veil_server_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.sudo('mkdir -p -m {:o} {}'.format(mode, '{}{}'.format(container_rootfs_path, remote_path)))
    fabric.api.sudo('chroot {} chown {}:{} {}'.format(container_rootfs_path, owner, owner_group, remote_path))


@atomic_installer
def veil_server_container_file_resource(local_path, veil_env_name, veil_server_name, remote_path, owner, owner_group, mode):
    container_rootfs_path = '/var/lib/lxc/{}-{}/rootfs'.format(veil_env_name, veil_server_name)
    full_remote_path = '{}{}'.format(container_rootfs_path, remote_path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container_file?{}-{}&path={}'.format(veil_env_name, veil_server_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.put(local_path, full_remote_path, use_sudo=True, mode=mode)
    fabric.api.sudo('chroot {} chown {}:{} {}'.format(container_rootfs_path, owner, owner_group, remote_path))


def remote_get_content(remote_path):
    return fabric.api.run('test -e {remote_path} && cat {remote_path}'.format(remote_path))


def remote_put_content(remote_path, content, **kwargs):
    temp_file_path = as_path(tempfile.mktemp())
    temp_file_path.write_text(content)
    fabric.api.put(temp_file_path, remote_path, **kwargs)


def render_installer_file(veil_env_name, veil_server_name):
    server = get_veil_server(veil_env_name, veil_server_name)
    host = get_veil_host(veil_env_name, server.host_name)
    veil_server_user_name = host.ssh_user
    container_name = '{}-{}'.format(veil_env_name, veil_server_name)
    mac_address = '{}:{}'.format(host.mac_prefix, server.sequence_no)
    ip_address = '{}.{}'.format(host.lan_range, server.sequence_no)
    gateway = '{}.1'.format(host.lan_range)

    iptables_rules = [
        'PREROUTING -d {}/32 -p tcp -m tcp --dport {}22 -j DNAT --to-destination {}:22'.format(host.internal_ip, server.sequence_no,
            ip_address),
        'POSTROUTING -s {}.0/24 ! -d {}.0/24 -j MASQUERADE'.format(host.lan_range, host.lan_range)
    ]
    installer_file_content = render_config('container-installer-file.j2', mac_address=mac_address, lan_interface=host.lan_interface,
        ip_address=ip_address, gateway=gateway, iptables_rules=iptables_rules, container_name=container_name, user_name=veil_server_user_name,
        name_servers=','.join(server.name_servers), memory_limit=server.memory_limit, cpu_share=server.cpu_share)
    lines = [installer_file_content]
    for resource in host.resources:
        installer_name, installer_args = resource
        line = '{}?{}'.format(installer_name, '&'.join('{}={}'.format(k, v) for k, v in installer_args.items()))
        lines.append(line)
    return '\n'.join(lines)