from __future__ import unicode_literals, print_function, division
import os
from time import sleep
import uuid
import fabric.api
import fabric.contrib.files
from veil.environment import *
from veil_component import as_path
from veil_installer import *
from .container_installer import veil_container_resource


CURRENT_DIR = as_path(os.path.dirname(__file__))
hosts_installed = []

@composite_installer
def veil_hosts_resource(veil_env_name, config_dir):
    resources = []
    for host in list_veil_hosts(veil_env_name).values():
        if host.base_name not in hosts_installed:
            resources.extend([
                veil_host_onetime_config_resource(host=host),
                veil_host_config_resource(host=host, config_dir=config_dir),
                veil_host_framework_codebase_resource(host=host)
            ])
            hosts_installed.append(host.base_name)
        for server in host.server_list:
            resources.append(veil_container_resource(host=host, server=server, config_dir=config_dir))
    return resources


@composite_installer
def veil_host_onetime_config_resource(host):
    fabric.api.env.host_string = '{}@{}:{}'.format(host.ssh_user, host.internal_ip, host.ssh_port)
    fabric.api.env.forward_agent = True
    installed = fabric.contrib.files.exists('/opt/veil-host-{}.initialized'.format(host.env_name))
    if installed:
        return []
    resources = [
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablesload', host=host, remote_path='/etc/network/if-pre-up.d/iptablesload',
            owner='root', owner_group='root', mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablessave', host=host, remote_path='/etc/network/if-post-down.d/iptablessave',
            owner='root', owner_group='root', mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'ipv4-ip-forward.conf', host=host, remote_path='/etc/sysctl.d/60-lxc-ipv4-ip-forward.conf',
            owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-lxc-ipv4-ip-forward.conf'),
        veil_host_file_resource(local_path=CURRENT_DIR / 'sudoers.d.ssh-auth-sock', host=host, remote_path='/etc/sudoers.d/ssh-auth-sock',
            owner='root', owner_group='root', mode=0440),
        veil_host_directory_resource(host=host, remote_path='/root/.ssh', owner='root', owner_group='root', mode=0755),
        veil_host_sources_list_resource(host=host)
    ]
    if VEIL_OS.codename == 'trusty':
        resources.append(veil_host_file_resource(local_path=CURRENT_DIR / 'lxc-net', host=host, remote_path='/etc/default/lxc-net',
            owner='root', owner_group='root', mode=0644))
    else:
        resources.append(veil_host_file_resource(local_path=CURRENT_DIR / 'lxc', host=host, remote_path='/etc/default/lxc',
            owner='root', owner_group='root', mode=0644))
    resources.append(veil_host_init_resource(host=host))
    return resources


@composite_installer
def veil_host_config_resource(host, config_dir):
    veil_server_user_name = host.ssh_user
    env_config_dir = config_dir / '{}'.format(host.env_name)
    resources = [
        veil_host_directory_resource(host=host, remote_path='/home/{}/.ssh'.format(veil_server_user_name), owner=veil_server_user_name,
            owner_group=veil_server_user_name, mode=0755),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'authorized_keys', host=host,
            remote_path='/home/{}/.ssh/authorized_keys'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name,
            mode=0644),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', host=host,
            remote_path='/home/{}/.ssh/known_hosts'.format(veil_server_user_name), owner=veil_server_user_name, owner_group=veil_server_user_name,
            mode=0644),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', host=host, remote_path='/root/.ssh/known_hosts',
            owner=veil_server_user_name, owner_group=veil_server_user_name, mode=0644),
        veil_host_file_resource(local_path=CURRENT_DIR / 'apt-config', host=host, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config',
            owner='root', owner_group='root', mode=0644),
        veil_host_sources_list_resource(host=host)
    ]
    return resources


@atomic_installer
def veil_host_framework_codebase_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_framework_codebase?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return
    clone_veil()
    with fabric.api.cd('/opt/veil'):
        pull_veil()
        fabric.api.sudo('./bin/veil init')


def clone_veil():
    if fabric.contrib.files.exists('/opt/veil'):
        return
    fabric.api.sudo('git clone {} /opt/veil'.format(VEIL_FRAMEWORK_CODEBASE))


def pull_veil():
    while True:
        try:
            fabric.api.sudo('git pull --rebase')
        except:
            sleep(2)
            continue
        else:
            break


@atomic_installer
def veil_host_init_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_init?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.sudo('apt-get -q update')
    fabric.api.sudo('apt-get -q -y purge ntp whoopsie network-manager')
    fabric.api.sudo('apt-get -q -y install ntpdate unattended-upgrades iptables git-core language-pack-en unzip wget python python-pip python-virtualenv lxc')
    fabric.api.sudo(
        '''printf '#!/bin/sh\n/usr/sbin/ntpdate ntp.ubuntu.com time.nist.gov' > /etc/cron.hourly/ntpdate && chmod 755 /etc/cron.hourly/ntpdate''',
        capture=True) # enable time sync on lxc hosts, and which is shared among lxc guests
    fabric.api.sudo('mkdir -p {}'.format(PYPI_ARCHIVE_DIR))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "setuptools>=3.6"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "pip>=1.5.6"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "virtualenv>=1.11.6"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('touch /opt/veil-host-{}.initialized'.format(host.env_name))


hosts_installed_sources_list = []

@atomic_installer
def veil_host_sources_list_resource(host):
    if host.name in hosts_installed_sources_list:
        return
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_sources_list?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return
    sources_list_path = '/etc/apt/sources.list'
    fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=sources_list_path))
    context = dict(mirror=VEIL_APT_URL, codename=fabric.api.run('lsb_release -cs'))
    fabric.contrib.files.upload_template('sources.list.j2', sources_list_path, context=context, use_jinja=True, template_dir=CURRENT_DIR,
        use_sudo=True, backup=False, mode=0644)
    hosts_installed_sources_list.append(host.name)


@atomic_installer
def veil_host_directory_resource(host, remote_path, owner, owner_group, mode):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_directory?{}&path={}'.format(host.env_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.sudo('mkdir -p -m {:o} {}'.format(mode, remote_path))
    fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))


@atomic_installer
def veil_host_file_resource(local_path, host, remote_path, owner, owner_group, mode, set_owner_first=False, cmd=None):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_file?{}&path={}'.format(host.env_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=remote_path))
    if set_owner_first:
        temp_file = '/tmp/{}'.format(uuid.uuid4().get_hex())
        fabric.api.put(local_path, temp_file, use_sudo=True, mode=mode)
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, temp_file))
        fabric.api.sudo('mv -f {} {}'.format(temp_file, remote_path))
    else:
        fabric.api.put(local_path, remote_path, use_sudo=True, mode=mode)
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))
    if cmd:
        fabric.api.sudo(cmd)
