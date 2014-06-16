from __future__ import unicode_literals, print_function, division
import os
from time import sleep
import uuid
import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil.environment import *
from veil.utility.misc import *
from veil_installer import *
from .container_installer import veil_container_resource, get_remote_file_content


CURRENT_DIR = as_path(os.path.dirname(__file__))
hosts_to_install = []
hosts_configured = []


@composite_installer
def veil_hosts_resource(veil_env_name, config_dir):
    resources = []
    for host in list_veil_hosts(veil_env_name):
        if host.base_name not in hosts_to_install:
            resources.extend([
                veil_host_onetime_config_resource(host=host, config_dir=config_dir),
                veil_host_config_resource(host=host, config_dir=config_dir),
                veil_host_application_codebase_resource(host=host)
            ])
            if host.has_user_editor:
                resources.append(veil_host_user_editor_resource(host=host, config_dir=config_dir))
            hosts_to_install.append(host.base_name)
        for server in host.server_list:
            resources.extend([
                veil_host_directory_resource(host=host, remote_path=host.etc_dir / server.name, owner='root', owner_group='root', mode=0755),
                veil_host_directory_resource(host=host, remote_path=host.log_dir / server.name, owner=host.ssh_user, owner_group=host.ssh_user_group,
                    mode=0755),
                veil_container_resource(host=host, server=server, config_dir=config_dir)
            ])
    return resources


@composite_installer
def veil_hosts_application_codebase_resource(veil_env_name):
    return [veil_host_application_codebase_resource(host=host) for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name)]


@composite_installer
def veil_host_onetime_config_resource(host, config_dir):
    fabric.api.env.host_string = host.deploys_via
    fabric.api.env.forward_agent = True

    initialized = fabric.contrib.files.exists(host.initialized_tag_path)
    if initialized:
        return []

    resources = [
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablesload', host=host, remote_path='/etc/network/if-pre-up.d/iptablesload',
            owner='root', owner_group='root', mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablessave', host=host, remote_path='/etc/network/if-post-down.d/iptablessave',
            owner='root', owner_group='root', mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'sudoers.d.ssh-auth-sock', host=host, remote_path='/etc/sudoers.d/ssh-auth-sock',
            owner='root', owner_group='root', mode=0440),
        veil_host_file_resource(local_path=CURRENT_DIR / 'ipv4-ip-forward.conf', host=host, remote_path='/etc/sysctl.d/60-lxc-ipv4-ip-forward.conf',
            owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-lxc-ipv4-ip-forward.conf'),
        veil_host_directory_resource(host=host, remote_path='/root/.ssh', owner='root', owner_group='root', mode=0755),
        veil_host_config_resource(host=host, config_dir=config_dir),
        veil_host_init_resource(host=host)
    ]
    return resources


@composite_installer
def veil_host_config_resource(host, config_dir):
    if host.base_name in hosts_configured:
        return []

    env_config_dir = config_dir / host.env_name
    resources = [
        veil_host_directory_resource(host=host, remote_path='/home/{}/.ssh'.format(host.ssh_user), owner=host.ssh_user,
            owner_group=host.ssh_user_group, mode=0755),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'authorized_keys', host=host,
            remote_path='/home/{}/.ssh/authorized_keys'.format(host.ssh_user), owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0644),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', host=host,
            remote_path='/home/{}/.ssh/known_hosts'.format(host.ssh_user), owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0644),
        veil_host_file_resource(local_path=env_config_dir / '.ssh' / 'known_hosts', host=host, remote_path='/root/.ssh/known_hosts',
            owner='root', owner_group='root', mode=0644),
        veil_host_file_resource(local_path=CURRENT_DIR / 'apt-config', host=host, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config',
            owner='root', owner_group='root', mode=0644),
        veil_host_sources_list_resource(host=host)
    ]
    if (env_config_dir / '.config').exists():
        resources.append(veil_host_file_resource(local_path=env_config_dir / '.config', host=host,
            remote_path='/home/{}/.config-{}'.format(host.ssh_user, host.env_name), owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0600))

    hosts_configured.append(host.base_name)
    return resources


@atomic_installer
def veil_host_application_codebase_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_application_codebase?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return
    clone_application(host)
    pull_application(host)
    clone_framework(host)
    pull_framework(host)
    init_application(host)


def clone_application(host):
    if fabric.contrib.files.exists(host.veil_home):
        return
    fabric.api.sudo('git clone {} {}'.format(get_application_codebase(), host.veil_home))


def clone_framework(host):
    if fabric.contrib.files.exists(host.veil_framework_home):
        return
    fabric.api.sudo('git clone {} {}'.format(VEIL_FRAMEWORK_CODEBASE, host.veil_framework_home))


def pull_application(host):
    with fabric.api.cd(host.veil_home):
        fabric.api.sudo('git checkout {}'.format(host.veil_application_branch))
        while True:
            try:
                fabric.api.sudo('git pull --rebase')
            except:
                sleep(1)
                continue
            else:
                break


def pull_framework(host):
    with fabric.api.cd(host.veil_framework_home):
        fabric.api.sudo('git checkout {}'.format(read_veil_framework_version(host)))
        while True:
            try:
                fabric.api.sudo('git pull --rebase')
            except:
                sleep(1)
                continue
            else:
                break


def init_application(host):
    with fabric.api.cd(host.veil_home):
        fabric.api.sudo('{}/bin/veil :{} init'.format(host.veil_framework_home, host.env_name))


def read_veil_framework_version(host):
    return get_remote_file_content(host.veil_home / 'VEIL-VERSION') or 'master'


@atomic_installer
def veil_host_init_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_init?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return

    fabric.contrib.files.append('/etc/ssh/sshd_config', 'PasswordAuthentication no', use_sudo=True)
    fabric.api.sudo('service ssh reload')

    fabric.api.sudo('apt-get -q update')
    fabric.api.sudo('apt-get -q -y purge ntp whoopsie network-manager')
    fabric.api.sudo('apt-get -q -y install ntpdate unattended-upgrades iptables git-core language-pack-en unzip wget python python-dev python-pip python-virtualenv lxc')
    # enable time sync on lxc hosts, and which is shared among lxc guests
    fabric.api.sudo(
        '''printf '#!/bin/sh\n/usr/sbin/ntpdate ntp.ubuntu.com time.nist.gov' > /etc/cron.hourly/ntpdate && chmod 755 /etc/cron.hourly/ntpdate''')
    fabric.api.sudo('mkdir -p -m 0755 {}'.format(' '.join([DEPENDENCY_DIR, DEPENDENCY_INSTALL_DIR, PYPI_ARCHIVE_DIR, host.code_dir, host.etc_dir,
        host.editorial_dir, host.buckets_dir, host.data_dir, host.log_dir])))
    fabric.api.sudo('chown {}:{} {} {}'.format(host.ssh_user, host.ssh_user_group, host.buckets_dir, host.data_dir))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "setuptools>=4.0.1"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "pip>=1.5.6"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))
    fabric.api.sudo('pip install -i {} --download-cache {} --upgrade "virtualenv>=1.11.6"'.format(PYPI_INDEX_URL, PYPI_ARCHIVE_DIR))

    install_resource(veil_lxc_config_resource(host=host))

    fabric.api.sudo('touch {}'.format(host.initialized_tag_path))


@atomic_installer
def veil_host_sources_list_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_sources_list?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return
    sources_list_path = '/etc/apt/sources.list'
    fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=sources_list_path))
    context = dict(mirror=APT_URL, codename=fabric.api.run('lsb_release -cs'))
    fabric.contrib.files.upload_template('sources.list.j2', sources_list_path, context=context, use_jinja=True, template_dir=CURRENT_DIR,
        use_sudo=True, backup=False, mode=0644)
    fabric.api.sudo('chown root:root {}'.format(sources_list_path))


@atomic_installer
def veil_lxc_config_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_lxc_config?{}'.format(host.env_name)
        dry_run_result[key] = 'INSTALL'
        return

    is_precise = fabric.api.run('lsb_release -cs') == 'precise'
    lxc_config_path = '/etc/default/lxc'
    fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=lxc_config_path))
    context = dict(is_precise=is_precise, mirror=APT_URL)
    fabric.contrib.files.upload_template('lxc.j2', lxc_config_path, context=context, use_jinja=True, template_dir=CURRENT_DIR,
        use_sudo=True, backup=False, mode=0644)
    fabric.api.sudo('chown root:root {}'.format(lxc_config_path))
    if not is_precise:
        install_resource(veil_host_file_resource(local_path=CURRENT_DIR / 'lxc-net', host=host, remote_path='/etc/default/lxc-net',
            owner='root', owner_group='root', mode=0644, keep_origin=True))


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
def veil_host_file_resource(local_path, host, remote_path, owner, owner_group, mode, keep_origin=False, set_owner_first=False, cmd=None):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_file?{}&path={}'.format(host.env_name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    if keep_origin:
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


@atomic_installer
def veil_host_user_editor_resource(host, config_dir):
    try:
        fabric.api.run('getent passwd editor')
    except:
        installed = False
    else:
        installed = True
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_user_editor?{}'.format(host.env_name)
        dry_run_result[key] = '-' if installed else 'INSTALL'
        return

    fabric.api.sudo('adduser editor --gecos editor --disabled-login --shell /usr/sbin/nologin --quiet')

    fabric.api.sudo('mkdir /home/editor/.ssh')
    fabric.api.put(config_dir / host.env_name / 'hosts' / host.base_name / 'editor-id_rsa.pub', '/home/editor/.ssh/authorized_keys', use_sudo=True,
        mode=0400)
    fabric.api.sudo('chown -R editor:editor /home/editor/.ssh')

    fabric.contrib.files.append('/etc/ssh/sshd_config',
        ['Match User editor', 'ChrootDirectory {}'.format(host.editorial_dir), 'ForceCommand internal-sftp'], use_sudo=True)
    fabric.api.sudo('service ssh reload')