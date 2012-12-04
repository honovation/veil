from __future__ import unicode_literals, print_function, division
import logging
import os
import fabric.api
import fabric.state
import tempfile
from veil_installer import *
from veil.utility.path import *
from veil.environment import *
from veil.server.config import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'container_installer_payload.py')
LOGGER = logging.getLogger(__name__)

@composite_installer
def veil_env_containers_resource(veil_env_name, config_dir):
    resources = []
    for veil_server_name in list_veil_servers(veil_env_name).keys():
        server_config_dir = as_path('{}/env/{}/{}'.format(config_dir, veil_env_name, veil_server_name))
        resources.append(veil_server_container_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name))
        resources.append(veil_server_container_config_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            server_config_dir=server_config_dir))
    return resources


@atomic_installer
def veil_server_container_resource(veil_env_name, veil_server_name):
    veil_server = get_veil_server(veil_env_name, veil_server_name)
    veil_host = get_veil_host(veil_env_name, veil_server.hosted_on)
    fabric.state.env.host_string = '{}:{}'.format(veil_host.ssh_ip, veil_host.ssh_port)
    fabric.state.env.user = veil_host.ssh_user
    veil_server_user_name = veil_host.ssh_user
    installer_file_content = render_installer_file(
        veil_env_name, veil_server_name, veil_server.sequence_no, veil_server_user_name)
    installer_file_path = '/opt/INSTALLER-{}-{}'.format(veil_env_name, veil_server_name)
    is_installed = installer_file_content == remote_get_content('{}.installed'.format(installer_file_path))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container?{}-{}'.format(veil_env_name, veil_server_name)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    remote_put_content(installer_file_path, installer_file_content, use_sudo=True, mode=0600)
    fabric.api.put(PAYLOAD, '/opt/container_installer_payload.py', use_sudo=True, mode=0600)
    fabric.api.sudo('python /opt/container_installer_payload.py {}'.format(installer_file_path))


@composite_installer
def veil_server_container_config_resource(veil_env_name, veil_server_name, server_config_dir):
    veil_server = get_veil_server(veil_env_name, veil_server_name)
    veil_host = get_veil_host(veil_env_name, veil_server.hosted_on)
    veil_server_user_name = veil_host.ssh_user
    resources = [
        veil_server_container_directory_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0755),
        veil_server_container_file_resource(
            local_path=server_config_dir / 'authorized_keys',
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh/authorized_keys'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644)]
    if (server_config_dir / 'config').exists():
        for local_path in (server_config_dir / 'config').listdir():
            remote_path = 'home/{}/{}'.format(veil_server_user_name, local_path.name)
            resources.append(veil_server_container_file_resource(
                local_path=local_path, veil_env_name=veil_env_name,
                veil_server_name=veil_server_name, remote_path=remote_path,
                owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0600))
    if (server_config_dir / 'known_hosts').exists():
        local_path = server_config_dir / 'known_hosts'
        resources.append(veil_server_container_file_resource(
            local_path=local_path, veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/home/{}/.ssh/known_hosts'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644))
        resources.append(veil_server_container_directory_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/root/.ssh',
            owner='root', owner_group='root', mode=0755))
        resources.append(veil_server_container_file_resource(
            local_path=local_path, veil_env_name=veil_env_name, veil_server_name=veil_server_name,
            remote_path='/root/.ssh/known_hosts',
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644))
    return resources


@atomic_installer
def veil_server_container_directory_resource(
        veil_env_name, veil_server_name, remote_path, owner, owner_group, mode):
    container_rootfs_path = '/var/lib/lxc/{}-{}/rootfs'.format(veil_env_name, veil_server_name)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container_directory?{}-{}&path={}'.format(veil_env_name, veil_server_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.state.env.warn_only = True
    try:
        fabric.api.sudo('mkdir -m {:o} {}'.format(mode, '{}{}'.format(container_rootfs_path, remote_path)))
    finally:
        fabric.state.env.warn_only = False
    fabric.api.sudo('chroot {} chown {} {}'.format(container_rootfs_path, owner, remote_path))
    fabric.api.sudo('chroot {} chgrp {} {}'.format(container_rootfs_path, owner_group, remote_path))


@atomic_installer
def veil_server_container_file_resource(
        local_path, veil_env_name, veil_server_name, remote_path, owner, owner_group, mode):
    container_rootfs_path = '/var/lib/lxc/{}-{}/rootfs'.format(veil_env_name, veil_server_name)
    full_remote_path = '{}{}'.format(container_rootfs_path, remote_path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_server_container_file?{}-{}&path={}'.format(veil_env_name, veil_server_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.put(local_path, full_remote_path, use_sudo=True, mode=mode)
    fabric.api.sudo('chroot {} chown {} {}'.format(container_rootfs_path, owner, remote_path))
    fabric.api.sudo('chroot {} chgrp {} {}'.format(container_rootfs_path, owner_group, remote_path))


def remote_get_content(remote_path):
    fabric.state.env.warn_only = True
    try:
        return fabric.api.run('cat {}'.format(remote_path))
    finally:
        fabric.state.env.warn_only = False


def remote_put_content(remote_path, content, **kwargs):
    temp_file_path = as_path(tempfile.mktemp())
    temp_file_path.write_text(content)
    fabric.api.put(temp_file_path, remote_path, **kwargs)


def render_installer_file(veil_env_name, veil_server_name, sequence_no, user_name):
    container_name = '{}-{}'.format(veil_env_name, veil_server_name)
    mac_address = '00:16:3e:73:bb:{}'.format(sequence_no)
    ip_address = '10.0.3.{}'.format(sequence_no)
    iptables_rule = 'PREROUTING -p tcp -m tcp --dport {}22 -j DNAT --to-destination 10.0.3.{}:22'.format(
        sequence_no, sequence_no)
    return render_config(
        'container-installer-file.j2', mac_address=mac_address, ip_address=ip_address,
        iptables_rule=iptables_rule, container_name=container_name, user_name=user_name)




