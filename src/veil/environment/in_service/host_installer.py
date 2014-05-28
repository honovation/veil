from __future__ import unicode_literals, print_function, division
import os
import uuid
import fabric.api
from veil_component import as_path
from veil.environment import *
from veil_installer import *
from veil.server.config import *


@composite_installer
def veil_env_hosts_resource(veil_env_name, config_dir):
    resources = []
    for veil_host_name in list_veil_hosts(veil_env_name):
        veil_host_base_name = veil_host_name.split('/')[0]  # e.g. ljhost-005/3 => ljhost-005
        host_config_dir = as_path('{}/host/{}'.format(config_dir, veil_host_base_name))
        resources.append(veil_host_config_resource(veil_env_name=veil_env_name, veil_host_name=veil_host_name, host_config_dir=host_config_dir))
    return resources


@composite_installer
def veil_host_config_resource(veil_env_name, veil_host_name, host_config_dir):
    host = get_veil_host(veil_env_name, veil_host_name)
    fabric.api.env.host_string = '{}@{}:{}'.format(host.ssh_user, host.internal_ip, host.ssh_port)
    veil_server_user_name = host.ssh_user
    resources = [
        veil_host_file_resource(
            local_path=host_config_dir / 'iptables' / 'iptablesload',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/etc/network/if-pre-up.d/iptablesload',
            owner='root', owner_group='root', mode=0755
        ),
        veil_host_file_resource(
            local_path=host_config_dir / 'iptables' / 'iptablessave',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/etc/network/if-post-down.d/iptablessave',
            owner='root', owner_group='root', mode=0755
        ),
        veil_host_file_resource(
            local_path=host_config_dir / 'sudoers.d.ssh-auth-sock',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/etc/sudoers.d/ssh-auth-sock',
            owner='root', owner_group='root', mode=0440
        ),
        veil_host_directory_resource(
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/home/{}/.ssh'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0755
        ),
        veil_host_file_resource(
            local_path=host_config_dir / 'authorized_keys',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/home/{}/.ssh/authorized_keys'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644
        ),
        veil_host_file_resource(
            local_path=host_config_dir / 'known_hosts',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/home/{}/.ssh/known_hosts'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644
        ),
        veil_host_directory_resource(
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/root/.ssh',
            owner='root', owner_group='root', mode=0755
        ),
        veil_host_file_resource(
            local_path=host_config_dir / 'known_hosts',
            veil_env_name=veil_env_name, veil_host_name=veil_host_name,
            remote_path='/root/.ssh/known_hosts',
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644
        )
    ]
    if host.override_sources_list:
        veil_host_os_codename = fabric.api.run('lsb_release -cs')
        with open('/tmp/veil_host_sources_list', mode='wb+') as f:
            f.write(render_config('sources.list.j2', mirror=VEIL_APT_URL, codename=veil_host_os_codename))
        resources.append(veil_host_file_resource(
            local_path='/tmp/veil_host_sources_list',
            veil_env_name=veil_env_name, veil_host_name=veil_env_name,
            remote_path='/etc/apt/sources.list',
            owner='root', owner_group='root', mode=0644
        ))
    if host.enable_unattended_upgrade:
        fabric.api.sudo('apt-get -q -y install unattended-upgrades')
        fabric.api.put(os.path.join(os.path.dirname(__file__), '50unattended-upgrades'), '/etc/apt/apt.conf.d/50unattended-upgrades', use_sudo=True,
            mode=0644)
        fabric.api.put(os.path.join(os.path.dirname(__file__), '99-update-and-download-daily'), '/etc/apt/apt.conf.d/99-update-and-download-daily',
            use_sudo=True, mode=0644)
        fabric.api.sudo('chown -R root:root /etc/apt/apt.conf.d/')
    return resources


@atomic_installer
def veil_host_directory_resource(veil_env_name, veil_host_name, remote_path, owner, owner_group, mode):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_directory?{}-{}&path={}'.format(veil_env_name, veil_host_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.sudo('mkdir -p -m {:o} {}'.format(mode, remote_path))
    fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))


@atomic_installer
def veil_host_file_resource(local_path, veil_env_name, veil_host_name, remote_path, owner, owner_group, mode, set_owner_first=False):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_file?{}-{}&path={}'.format(veil_env_name, veil_host_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    if set_owner_first:
        temp_file = '/tmp/{}'.format(uuid.uuid4().get_hex())
        fabric.api.put(local_path, temp_file, use_sudo=True, mode=mode)
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, temp_file))
        fabric.api.sudo('mv -f {} {}'.format(temp_file, remote_path))
    else:
        fabric.api.put(local_path, remote_path, use_sudo=True, mode=mode)
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))
