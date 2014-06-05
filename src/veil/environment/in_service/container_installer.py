from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import os
import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil_installer import *
from veil.environment import *
from veil.server.config import *

CURRENT_DIR = as_path(os.path.dirname(__file__))


@composite_installer
def veil_container_resource(host, server, config_dir):
    resources = [
        veil_container_lxc_resource(host=host, server=server),
        veil_container_onetime_config_resource(server=server),
        veil_container_config_resource(host=host, server=server, config_dir=config_dir)
    ]
    return resources


def get_remote_file_content(remote_path):
    content = None
    if fabric.contrib.files.exists(remote_path):
        f = StringIO()
        fabric.api.get(remote_path, f)
        content = f.getvalue()
    return content


@atomic_installer
def veil_container_lxc_resource(host, server):
    installer_file_path = '/opt/veil-container-INSTALLER-{}'.format(server.container_name)
    installed_installer_file_path = '{}.installed'.format(installer_file_path)
    remote_installer_file_content = get_remote_file_content(installed_installer_file_path)
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
    fabric.api.put(StringIO(installer_file_content), installer_file_path, use_sudo=True, mode=0600)
    with fabric.api.cd('/opt/veil'):
        fabric.api.sudo('veil install veil_installer.installer_resource?{}'.format(installer_file_path))
    fabric.api.sudo('mv -f {} {}'.format(installer_file_path, installed_installer_file_path))


@composite_installer
def veil_container_onetime_config_resource(server):
    installed = fabric.contrib.files.exists('/opt/veil-container-{}.initialized'.format(server.container_name))
    if installed:
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
        veil_container_directory_resource(server=server, remote_path='/root/.ssh', owner='root', owner_group='root', mode=0755),
        veil_container_sources_list_resource(server=server),
        veil_container_init_resource(server=server)
    ]
    return resources


@atomic_installer
def veil_container_init_resource(server):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_init?{}'.format(server.container_name)
        dry_run_result[key] = 'INSTALL'
        return
    container_rootfs_path = '/var/lib/lxc/{}/rootfs'.format(server.container_name)
    fabric.api.sudo('chroot {} apt-get -q update'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt-get -q -y purge ntpdate ntp whoopsie network-manager'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} apt-get -q -y install unattended-upgrades iptables git-core language-pack-en unzip wget python python-pip python-virtualenv'.format(container_rootfs_path))
    fabric.api.sudo('chroot {} mkdir -p {}'.format(container_rootfs_path, VEIL_TMP_DIR))
    fabric.api.sudo('chroot {} mkdir -p {}'.format(container_rootfs_path, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "setuptools>=3.6"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "pip>=1.5.6"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('chroot {} pip install -i {} --download-cache {} --upgrade "virtualenv>=1.11.6"'.format(container_rootfs_path, PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('touch /opt/veil-container-{}.initialized'.format(server.container_name))


@composite_installer
def veil_container_config_resource(host, server, config_dir):
    veil_server_user_name = host.ssh_user
    env_config_dir = config_dir / server.env_name
    server_config_dir = env_config_dir / 'servers' / server.name
    resources = [
        veil_server_boot_script_resource(server=server),
        veil_container_directory_resource(server=server, remote_path='/home/{}/.ssh'.format(veil_server_user_name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0755),
        veil_container_file_resource(local_path=env_config_dir / '.ssh' / 'authorized_keys', server=server,
            remote_path='/home/{}/.ssh/authorized_keys'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name,
            mode=0644),
        veil_container_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', server=server,
            remote_path='/home/{}/.ssh/known_hosts'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name,
            mode=0644),
        veil_container_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', server=server, remote_path='/root/.ssh/known_hosts',
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644),
        veil_container_file_resource(local_path=CURRENT_DIR / 'apt-config', server=server, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config',
            owner='root', owner_group='root', mode=0644),
        veil_container_sources_list_resource(server=server)
    ]
    if (env_config_dir / '.config').exists():
        resources.append(veil_container_file_resource(local_path=env_config_dir / '.config', server=server,
            remote_path='/home/{}/.config'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0600))
    for local_path in server_config_dir.files('*.crt'):
        resources.append(veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/certs/{}'.format(local_path.name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644))
    for local_path in server_config_dir.files('*.key'):
        resources.append(veil_container_file_resource(local_path=local_path, server=server, remote_path='/etc/ssl/private/{}'.format(local_path.name),
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0640))
    if (server_config_dir / '.ssh' / 'id_rsa').exists():
        resources.append(veil_container_file_resource(local_path=server_config_dir / '.ssh' / 'id_rsa', server=server,
            remote_path='/home/{}/.ssh/id_rsa'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name,
            mode=0600))
        resources.append(veil_container_file_resource(local_path=server_config_dir / '.ssh' / 'id_rsa', server=server,
            remote_path='/root/.ssh/id_rsa', owner='root', owner_group='root', mode=0600))
    return resources


servers_installed_sources_list = []

@atomic_installer
def veil_container_sources_list_resource(server):
    if server.container_name in servers_installed_sources_list:
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
    context = dict(mirror=VEIL_APT_URL, codename=fabric.api.run('lsb_release -cs')) # Assumption: lxc container has same os version as host
    fabric.contrib.files.upload_template('sources.list.j2', full_sources_list_path, context=context, use_jinja=True, template_dir=CURRENT_DIR,
        use_sudo=True, backup=False, mode=0644)
    servers_installed_sources_list.append(server.container_name)


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
    fabric.api.put(StringIO(boot_script_content), full_boot_script_path, use_sudo=True, mode=0755)
    fabric.api.sudo('chroot {} chown root:root {}'.format(container_rootfs_path, boot_script_path))
    fabric.api.sudo('chroot {} update-rc.d {} defaults 90 10'.format(container_rootfs_path, server.container_name))


def render_veil_server_boot_script(server):
    return render_config('veil-server-boot-script.j2', script_name=server.container_name,
        do_start_command='cd /opt/{env_name}/app && sudo veil :{env_name}/{} up --daemonize'.format(server.name, env_name=server.env_name),
        do_stop_command='cd /opt/{env_name}/app && sudo veil :{env_name}/{} down'.format(server.name, env_name=server.env_name))


def render_installer_file(host, server):
    veil_server_user_name = host.ssh_user
    mac_address = '{}:{}'.format(host.mac_prefix, server.sequence_no)
    ip_address = '{}.{}'.format(host.lan_range, server.sequence_no)
    gateway = '{}.1'.format(host.lan_range)

    iptables_rules = [
        'PREROUTING -d {}/32 -p tcp -m tcp --dport {}22 -j DNAT --to-destination {}:22'.format(host.internal_ip, server.sequence_no, ip_address),
        'POSTROUTING -s {}.0/24 ! -d {}.0/24 -j MASQUERADE'.format(host.lan_range, host.lan_range)
    ]
    installer_file_content = render_config('container-installer-file.j2', mac_address=mac_address, lan_interface=host.lan_interface,
        ip_address=ip_address, gateway=gateway, iptables_rules=iptables_rules, container_name=server.container_name, user_name=veil_server_user_name,
        name_servers=','.join(server.name_servers), memory_limit=server.memory_limit, cpu_share=server.cpu_share)
    lines = [installer_file_content]
    for resource in host.resources:
        installer_name, installer_args = resource
        line = '{}?{}'.format(installer_name, '&'.join('{}={}'.format(k, v) for k, v in installer_args.items()))
        lines.append(line)
    return '\n'.join(lines)
