from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
import os
import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil_installer import *
from veil.server.config import *
from .server_installer import is_container_running

CURRENT_DIR = as_path(os.path.dirname(__file__))


@composite_installer
def veil_container_resource(host, server, config_dir):
    resources = [
        veil_container_lxc_resource(host=host, server=server),
        veil_container_config_resource(server=server, config_dir=config_dir),
        veil_container_onetime_config_resource(server=server)
    ]
    return resources


def get_remote_file_content(remote_path):
    content = None
    if fabric.contrib.files.exists(remote_path, use_sudo=True):
        with contextlib.closing(StringIO()) as f:
            fabric.api.get(remote_path, local_path=f, use_sudo=True)
            content = f.getvalue()
    return content


@atomic_installer
def veil_container_lxc_resource(host, server):
    remote_installer_file_content = get_remote_file_content(server.installed_container_installer_path)
    installer_file_content = render_installer_file(host, server)
    if remote_installer_file_content:
        action = None if installer_file_content == remote_installer_file_content else 'UPDATE'
    else:
        action = 'INSTALL'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container?{}'.format(server.container_name)
        dry_run_result[key] = action or '-'
        return
    if not action:
        if not is_container_running(server):
            fabric.api.sudo('lxc-start -n {} -d'.format(server.container_name))
        return
    with contextlib.closing(StringIO(installer_file_content)) as f:
        fabric.api.put(f, server.container_installer_path, use_sudo=True, mode=0600)
    with fabric.api.cd(host.veil_home):
        fabric.api.sudo('veil :{} install veil_installer.installer_resource?{}'.format(server.fullname, server.container_installer_path))
    fabric.api.sudo('mv -f {} {}'.format(server.container_installer_path, server.installed_container_installer_path))


@composite_installer
def veil_container_onetime_config_resource(server):
    initialized = fabric.contrib.files.exists(server.container_initialized_tag_path)
    if initialized:
        return []

    resources = [
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablesload', server=server, remote_path='/etc/network/if-pre-up.d/iptablesload', owner='root',
                                     owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablessave', server=server, remote_path='/etc/network/if-post-down.d/iptablessave',
                                     owner='root', owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'sudoers.d.no-password', server=server, remote_path='/etc/sudoers.d/no-password', owner='root',
                                     owner_group='root', mode=0440),
        veil_container_init_resource(server=server)
    ]
    return resources


@composite_installer
def veil_container_config_resource(server, config_dir):
    env_config_dir = config_dir / server.VEIL_ENV.name
    server_config_dir = env_config_dir / 'servers' / server.name
    resources = [
        veil_server_default_setting_resource(server=server),
        veil_server_boot_script_resource(server=server),
        veil_container_file_resource(local_path=CURRENT_DIR / 'apt-config', server=server, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config', owner='root',
                                     owner_group='root', mode=0644)
    ]
    if 'guard' == server.name:
        resources.append(veil_container_file_resource(local_path=env_config_dir / '.ssh-guard' / 'id_rsa', server=server, remote_path='/etc/ssh/id_rsa-guard',
                                                      owner='root', owner_group='root', mode=0600))
    if 'barman' == server.name:
        resources.append(veil_container_file_resource(local_path=env_config_dir / '.ssh-guard' / 'id_rsa', server=server,
                                                      remote_path='/etc/ssh/id_rsa-barman'.format(server.ssh_user),
                                                      owner=server.ssh_user, owner_group=server.ssh_user_group, mode=0600))
    for local_path in server_config_dir.files('*.crt'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0644))
    for local_path in server_config_dir.files('*.cert.pem'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0644))
    for local_path in server_config_dir.files('*.key'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/private/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0600))
    for local_path in server_config_dir.files('*.key.pem'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/private/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0600))
    for local_path in server_config_dir.files('*.pub.pem'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0400))
    for local_path in server_config_dir.files('*.pub.cer'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0400))
    for local_path in server_config_dir.files('*.pri.pem'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssh/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0400))
    for local_path in server_config_dir.files('*.pfx'):
        resources.append(
            veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssh/{}'.format(local_path.name), owner=server.ssh_user,
                                         owner_group=server.ssh_user_group, mode=0400))
    return resources


@atomic_installer
def veil_container_init_resource(server):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_init?{}'.format(server.container_name)
        dry_run_result[key] = 'INSTALL'
        return

    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)

    fabric.contrib.files.append('{}/etc/ssh/sshd_config'.format(container_rootfs_path), ['PasswordAuthentication no', 'PermitRootLogin no', 'UseDNS no'],
                                use_sudo=True)
    # fix error: Missing privilege separation directory: /var/run/sshd
    fabric.api.sudo('chroot {} mkdir /var/run/sshd'.format(container_rootfs_path), warn_only=True)
    fabric.api.sudo('chroot {} service ssh restart'.format(container_rootfs_path))

    fabric.api.sudo('chroot {} apt update'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt -y purge ntpdate ntp whoopsie network-manager'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt -y install apt-transport-https unattended-upgrades update-notifier-common iptables git language-pack-en unzip wget python python-dev python-pip python-virtualenv'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} pip install --upgrade "pip>=9.0.1"'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} pip install -i {} --trusted-host {} --upgrade "setuptools>=34.2.0"'.format(container_rootfs_path, server.pypi_index_url, server.pypi_index_host))
    fabric.api.sudo('chroot {} pip install -i {} --trusted-host {} --upgrade "wheel>=0.30.0a0"'.format(container_rootfs_path, server.pypi_index_url, server.pypi_index_host))
    fabric.api.sudo('chroot {} pip install -i {} --trusted-host {} --upgrade "virtualenv>=15.1.0"'.format(container_rootfs_path, server.pypi_index_url, server.pypi_index_host))
    fabric.api.sudo('lxc-attach -n {} -- systemctl enable veil-server.service'.format(server.container_name))
    fabric.api.sudo('touch {}'.format(server.container_initialized_tag_path))


@atomic_installer
def veil_container_directory_resource(server, remote_path, owner, owner_group, mode):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_directory?{}&path={}'.format(server.container_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    fabric.api.sudo('chroot {} mkdir -p {}'.format(container_rootfs_path, remote_path))
    fabric.api.sudo('chroot {} chmod {:o} {}'.format(container_rootfs_path, mode, remote_path))
    fabric.api.sudo('chroot {} chown {}:{} {}'.format(container_rootfs_path, owner, owner_group, remote_path))


@atomic_installer
def veil_container_file_resource(local_path, server, remote_path, owner, owner_group, mode, keep_origin=False):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_file?{}&path={}'.format(server.container_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    if keep_origin:
        fabric.api.sudo('chroot {} cp -pn {path} {path}.origin'.format(container_rootfs_path, path=remote_path))
    fabric.api.put(local_path, '{}{}'.format(container_rootfs_path, remote_path), use_sudo=True, mode=mode)
    fabric.api.sudo('chroot {} chown {}:{} {}'.format(container_rootfs_path, owner, owner_group, remote_path))


@atomic_installer
def veil_server_default_setting_resource(server):
    default_setting_path = '/etc/default/veil'
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    full_default_setting_path = '{}{}'.format(container_rootfs_path, default_setting_path)
    remote_default_setting_content = get_remote_file_content(full_default_setting_path)
    default_setting_content = render_veil_server_default_setting(server)

    if remote_default_setting_content:
        action = None if default_setting_content == remote_default_setting_content else 'UPDATE'
    else:
        action = 'INSTALL'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_app_default_setting?{}'.format(server.container_name)
        dry_run_result[key] = action or '-'
        return
    if not action:
        return
    print('{} veil server default setting: {} ...'.format(action, server.container_name))
    with contextlib.closing(StringIO(default_setting_content)) as f:
        fabric.api.put(f, full_default_setting_path, use_sudo=True, mode=0644)
    fabric.api.sudo('chroot {} chown root:root {}'.format(container_rootfs_path, default_setting_path))


@atomic_installer
def veil_server_boot_script_resource(server):
    boot_script_path = '/lib/systemd/system/veil-server.service'
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    full_boot_script_path = '{}{}'.format(container_rootfs_path, boot_script_path)

    remote_boot_script_content = get_remote_file_content(full_boot_script_path)
    boot_script_content = render_config('veil-server.service.j2', veil_home=server.veil_home)

    if remote_boot_script_content:
        action = None if boot_script_content == remote_boot_script_content else 'UPDATE'
    else:
        action = 'INSTALL'
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_app_boot_script?{}'.format(server.container_name)
        dry_run_result[key] = action or '-'
        return
    if not action:
        return
    print('{} boot script: {} ...'.format(action, server.container_name))

    with contextlib.closing(StringIO(boot_script_content)) as f:
        fabric.api.put(f, full_boot_script_path, use_sudo=True, mode=0644)
    fabric.api.sudo('chroot {} chown root:root {}'.format(container_rootfs_path, boot_script_path))
    fabric.api.sudo('lxc-attach -n {} -- systemctl daemon-reload'.format(server.container_name))


def render_veil_server_default_setting(server):
    return render_config('veil-server-settings.j2', veil_home=server.veil_home, veil_server=server.fullname)


def render_installer_file(host, server):
    mac_address = '{}:{}'.format(host.mac_prefix, server.sequence_no)
    ip_address = '{}.{}'.format(host.lan_range, server.sequence_no)
    gateway = '{}.1'.format(host.lan_range)
    installer_file_content = render_config('container-installer-file.j2', mac_address=mac_address, ip_address=ip_address, gateway=gateway, server=server,
                                           host=host)
    return installer_file_content
