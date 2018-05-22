from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
import os
from time import sleep

import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil_installer import *
from veil.server.config import *
from veil.environment.lxd import *
from .server_installer import is_container_running

CURRENT_DIR = as_path(os.path.dirname(__file__))


@composite_installer
def veil_container_resource(host, server):
    resources = [
        veil_container_lxc_resource(host=host, server=server),
        veil_container_config_resource(server=server),
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
            container = LXDClient(config_dir=server.env_config_dir).get_container(server.container_name)
            container.start()
    else:
        with contextlib.closing(StringIO(installer_file_content)) as f:
            fabric.api.put(f, server.container_installer_path, use_sudo=True, mode=0600)
        with fabric.api.cd(host.veil_home):
            fabric.api.run('veil :{} install veil_installer.installer_resource?{}'.format(server.fullname, server.container_installer_path))
        fabric.api.run('mv -f {} {}'.format(server.container_installer_path, server.installed_container_installer_path))
    while 1:
        try:
            with fabric.api.settings(host_string=server.deploys_via):
                fabric.api.sudo('sudo chown -R {}:{} {}'.format(server.ssh_user, server.ssh_user_group, host.env_dir))
                fabric.api.run('echo Server started!')
                break
        except Exception as e:
            print(e.message)
            print('waiting for server start...')
            sleep(1)


@composite_installer
def veil_container_onetime_config_resource(server):
    initialized = fabric.contrib.files.exists(server.container_initialized_tag_path)
    if initialized:
        return []

    resources = [
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablesload', server=server, remote_path='/usr/local/bin/iptablesload', owner='root',
                                     owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'iptablessave', server=server, remote_path='/usr/local/bin/iptablessave', owner='root',
                                     owner_group='root', mode=0755),
        veil_container_file_resource(local_path=CURRENT_DIR / 'persist-iptables.service', server=server,
                                     remote_path='/lib/systemd/system/persist-iptables.service', owner='root', owner_group='root', mode=0755,
                                     cmds=('systemctl daemon-reload', 'systemctl enable persist-iptables.service', 'systemctl start persist-iptables.service')),
        veil_container_init_resource(server=server)
    ]
    return resources


@atomic_installer
def veil_container_sources_list_resource(server):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_sources_list?{}'.format(server.name)
        dry_run_result[key] = 'INSTALL'
        return
    client = LXDClient(config_dir=server.env_config_dir)
    sources_list_path = '/etc/apt/sources.list'
    client.run_container_command(server.container_name, 'cp -pn {path} {path}.origin'.format(path=sources_list_path))
    codename = client.run_container_command(server.container_name, 'lsb_release -cs').strip()
    sources_list_content = render_config(CURRENT_DIR / 'sources.list.j2', mirror=server.apt_url, codename=codename)
    client.put_container_file(server.container_name, sources_list_path, sources_list_content)
    client.run_container_command(server.container_name, 'chown root:root {}'.format(sources_list_path))


@composite_installer
def veil_container_config_resource(server):
    server_config_dir = server.env_config_dir / 'servers' / server.name
    resources = [
        veil_server_default_setting_resource(server=server),
        veil_server_boot_script_resource(server=server),
        veil_container_file_resource(local_path=CURRENT_DIR / 'apt-config', server=server, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config', owner='root',
                                     owner_group='root', mode=0644),
        veil_container_sources_list_resource(server=server)
    ]
    if 'guard' == server.name:
        resources.append(veil_container_file_resource(local_path=server.env_config_dir / '.ssh-guard' / 'id_rsa', server=server,
                                                      remote_path='/etc/ssh/id_rsa-guard', owner='root', owner_group='root', mode=0600))
    if 'barman' == server.name:
        resources.append(veil_container_file_resource(local_path=server.env_config_dir / '.ssh-guard' / 'id_rsa', server=server,
                                                      remote_path='/etc/ssh/id_rsa-barman'.format(server.ssh_user),
                                                      owner=server.ssh_user, owner_group=server.ssh_user_group, mode=0600))
        resources.append(veil_container_file_resource(local_path='-', server=server, remote_path='/etc/cron.d/barman', owner='root', owner_group='root',
                                                      mode=0644, file_content=render_config(CURRENT_DIR / 'pg_barman_cron.d.j2', barman_user=server.ssh_user)))
        resources.append(veil_container_file_resource(local_path='-', server=server, remote_path='/etc/barman.conf', owner='root', owner_group='root',
                                                      mode=0644, file_content=render_config(CURRENT_DIR / 'pg_barman.conf.j2', barman_user=server.ssh_user,
                                                                                            server_conf_path=server.etc_dir / 'barman.d',
                                                                                            barman_home=server.var_dir / 'barman', log_path=server.log_dir)))
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
    package_names = ['apt-transport-https', 'unattended-upgrades', 'update-notifier-common', 'iptables', 'git', 'language-pack-en', 'unzip', 'wget', 'python',
                     'python-dev', 'python-pip', 'python-virtualenv']
    with fabric.api.settings(host_string=server.deploys_via):
        fabric.api.sudo('apt update')
        fabric.api.sudo('apt -y install {}'.format(' '.join(package_names)))
        fabric.api.sudo('apt -y purge ntpdate ntp whoopsie network-manager')
        fabric.api.run('touch {}'.format(server.container_initialized_tag_path))


@atomic_installer
def veil_container_file_resource(local_path, server, remote_path, owner, owner_group, mode, keep_origin=False, cmds=None, file_content=None):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_container_file?{}&path={}'.format(server.container_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    client = LXDClient(config_dir=server.env_config_dir)
    if keep_origin:
        client.run_container_command(server.container_name, 'cp -pn {path} {path}.origin'.format(path=remote_path))
    if not file_content:
        f = as_path(local_path)
        if not f.exists():
            raise Exception('file not exists: {}'.format(local_path))
        content = f.bytes()
    else:
        content = file_content
    client.put_container_file(server.container_name, remote_path, content, mode=mode)
    client.run_container_command(server.container_name, 'chown {}:{} {}'.format(owner, owner_group, remote_path))
    if cmds:
        for cmd in cmds:
            client.run_container_command(server.container_name, cmd)


@atomic_installer
def veil_server_default_setting_resource(server):
    default_setting_path = '/etc/default/veil'
    client = LXDClient(config_dir=server.env_config_dir)
    remote_default_setting_content = client.get_container_file_content(server.container_name, default_setting_path)
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
    client.put_container_file(server.container_name, default_setting_path, default_setting_content)


@atomic_installer
def veil_server_boot_script_resource(server):
    boot_script_path = '/lib/systemd/system/veil-server.service'
    client = LXDClient(config_dir=server.env_config_dir)
    remote_boot_script_content = client.get_container_file_content(server.container_name, boot_script_path)
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
    client.put_container_file(server.container_name, boot_script_path, boot_script_content)
    with fabric.api.settings(host_string=server.deploys_via):
        fabric.api.sudo('systemctl daemon-reload')
        fabric.api.sudo('systemctl enable veil-server')


def render_veil_server_default_setting(server):
    return render_config('veil-server-settings.j2', veil_home=server.veil_home, veil_server=server.fullname)


def render_installer_file(host, server):
    mac_address = '{}:{}'.format(host.mac_prefix, server.sequence_no)
    ip_address = '{}.{}'.format(host.lan_range, server.sequence_no)
    gateway = '{}.1'.format(host.lan_range)
    installer_file_content = render_config('container-installer-file.j2', mac_address=mac_address, ip_address=ip_address, gateway=gateway, server=server,
                                           host=host)
    return installer_file_content
