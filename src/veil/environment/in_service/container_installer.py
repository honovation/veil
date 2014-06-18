from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
import os
import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil_installer import *
from veil.environment import *
from veil.server.config import *

CURRENT_DIR = as_path(os.path.dirname(__file__))
sources_list_installed = []


@composite_installer
def veil_container_resource(host, server, config_dir):
    resources = [
        veil_container_lxc_resource(host=host, server=server),
        veil_container_onetime_config_resource(server=server, config_dir=config_dir),
        veil_container_config_resource(server=server, config_dir=config_dir)
    ]
    return resources


def get_remote_file_content(remote_path):
    content = None
    if fabric.contrib.files.exists(remote_path):
        with contextlib.closing(StringIO()) as f:
            fabric.api.get(remote_path, f)
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
        return
    with contextlib.closing(StringIO(installer_file_content)) as f:
        fabric.api.put(f, server.container_installer_path, use_sudo=True, mode=0600)
    with fabric.api.cd(host.veil_home):
        fabric.api.sudo('veil :{} install veil_installer.installer_resource?{}'.format(host.env_name, server.container_installer_path))
    fabric.api.sudo('mv -f {} {}'.format(server.container_installer_path, server.installed_container_installer_path))


@composite_installer
def veil_container_onetime_config_resource(server, config_dir):
    initialized = fabric.contrib.files.exists(server.container_initialized_tag_path)
    if initialized:
        return []

    resources = [
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablesload', server=server, remote_path='/etc/network/if-pre-up.d/iptablesload',
            owner='root', owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablessave', server=server, remote_path='/etc/network/if-post-down.d/iptablessave',
            owner='root', owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'sudoers.d.ssh-auth-sock', server=server, remote_path='/etc/sudoers.d/ssh-auth-sock',
            owner='root', owner_group='root', mode=0440),
        veil_container_file_resource(local_path=CURRENT_DIR / 'sudoers.d.no-password', server=server, remote_path='/etc/sudoers.d/no-password',
            owner='root', owner_group='root', mode=0440),
        veil_container_directory_resource(server=server, remote_path='/root/.ssh', owner='root', owner_group='root', mode=0700),
        veil_container_sources_list_resource(server=server),
        veil_container_init_resource(server=server)
    ]
    return resources


@composite_installer
def veil_container_config_resource(server, config_dir):
    env_config_dir = config_dir / server.env_name
    server_config_dir = env_config_dir / 'servers' / server.name
    resources = [
        veil_server_boot_script_resource(server=server),
        veil_container_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', server=server, remote_path='/root/.ssh/known_hosts',
            owner='root', owner_group='root', mode=0600),
        veil_container_file_resource(local_path=CURRENT_DIR / 'apt-config', server=server, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config',
            owner='root', owner_group='root', mode=0644),
        veil_container_sources_list_resource(server=server)
    ]
    for local_path in server_config_dir.files('*.crt'):
        resources.append(veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name),
            owner=server.ssh_user, owner_group=server.ssh_user_group, mode=0644))
    for local_path in server_config_dir.files('*.key'):
        resources.append(veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/private/{}'.format(local_path.name),
            owner=server.ssh_user, owner_group=server.ssh_user_group, mode=0600))
    if '@guard' == server.name:
        resources.append(veil_container_file_resource(local_path=server_config_dir / '.ssh' / 'id_rsa', server=server,
            remote_path='/etc/ssh/id_rsa-@guard', owner=server.ssh_user, owner_group=server.ssh_user_group, mode=0600))
    return resources


@atomic_installer
def veil_container_init_resource(server):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_init?{}'.format(server.container_name)
        dry_run_result[key] = 'INSTALL'
        return

    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)

    fabric.contrib.files.append('{}/etc/ssh/sshd_config'.format(container_rootfs_path),
        ['PasswordAuthentication no', 'GatewayPorts clientspecified', 'MaxSessions 128'], use_sudo=True)
    if 'precise' == fabric.api.sudo('chroot {} lsb_release -cs'.format(container_rootfs_path)):
        fabric.api.sudo('chroot {} /etc/init.d/ssh restart'.format(container_rootfs_path))
    else:
        fabric.api.sudo('chroot {} service ssh reload'.format(container_rootfs_path))

    fabric.api.sudo('chroot {} apt-get -q update'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt-get -q -y purge ntpdate ntp whoopsie network-manager'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt-get -q -y install unattended-upgrades iptables git-core language-pack-en unzip wget python python-dev python-pip python-virtualenv'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "setuptools>=4.0.1"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "pip>=1.5.6"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "virtualenv>=1.11.6"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('touch {}'.format(server.container_initialized_tag_path))


@atomic_installer
def veil_container_sources_list_resource(server):
    if server.name in sources_list_installed:
        return

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_sources_list?{}'.format(server.container_name)
        dry_run_result[key] = 'INSTALL'
        return
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    sources_list_path = '/etc/apt/sources.list'
    full_sources_list_path = '{}{}'.format(container_rootfs_path, sources_list_path)
    fabric.api.sudo('chroot {} cp -pn {path} {path}.origin'.format(container_rootfs_path, path=sources_list_path))
    context = dict(mirror=APT_URL, codename=fabric.api.sudo('chroot {} lsb_release -cs'.format(container_rootfs_path)))
    fabric.contrib.files.upload_template('sources.list.j2', full_sources_list_path, context=context, use_jinja=True, template_dir=CURRENT_DIR,
        use_sudo=True, backup=False, mode=0644)
    fabric.api.sudo('chroot {} chown root:root {}'.format(container_rootfs_path, sources_list_path))

    sources_list_installed.append(server.name)


@atomic_installer
def veil_container_directory_resource(server, remote_path, owner, owner_group, mode):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_directory?{}&path={}'.format(server.container_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    fabric.api.sudo('chroot {} mkdir -p -m {:o} {}'.format(container_rootfs_path, mode, remote_path))
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
def veil_server_boot_script_resource(server):
    boot_script_path = '/etc/init.d/{}'.format(server.container_name)
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    full_boot_script_path = '{}{}'.format(container_rootfs_path, boot_script_path)
    remote_boot_script_content = get_remote_file_content(full_boot_script_path)
    boot_script_content = render_veil_server_boot_script(server)
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
    fabric.api.sudo('chroot {} update-rc.d -f {} remove'.format(container_rootfs_path, server.container_name))
    with contextlib.closing(StringIO(boot_script_content)) as f:
        fabric.api.put(f, full_boot_script_path, use_sudo=True, mode=0755)
    fabric.api.sudo('chroot {} chown root:root {}'.format(container_rootfs_path, boot_script_path))
    fabric.api.sudo('chroot {} update-rc.d {} defaults 90 10'.format(container_rootfs_path, server.container_name))


def render_veil_server_boot_script(server):
    return render_config('veil-server-boot-script.j2', script_name=server.container_name,
        do_start_command='cd {} && sudo veil :{} up --daemonize'.format(server.veil_home, server.fullname),
        do_stop_command='cd {} && sudo veil :{} down'.format(server.veil_home, server.fullname))


def render_installer_file(host, server):
    mac_address = '{}:{}'.format(host.mac_prefix, server.sequence_no)
    ip_address = '{}.{}'.format(host.lan_range, server.sequence_no)
    gateway = '{}.1'.format(host.lan_range)

    iptables_rules = [
        'POSTROUTING -s {}.0/24 ! -d {}.0/24 -j MASQUERADE'.format(host.lan_range, host.lan_range)
    ]
    installer_file_content = render_config('container-installer-file.j2', mac_address=mac_address, ip_address=ip_address, gateway=gateway,
        iptables_rules=iptables_rules, server=server, host=host)
    lines = [installer_file_content]
    for resource in host.resources:
        installer_name, installer_args = resource
        line = '{}?{}'.format(installer_name, '&'.join('{}={}'.format(k, v) for k, v in installer_args.items()))
        lines.append(line)
    return '\n'.join(lines)
