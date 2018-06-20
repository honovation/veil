from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
import os
from time import sleep
import uuid
import logging
import fabric.api
import fabric.contrib.files
from veil.utility.setting import *
from veil_component import as_path, cyan
from veil.environment import *
from veil.environment.networking import *
from veil.environment.lxd import *
from veil.utility.misc import *
from veil_installer import *
from .container_installer import veil_container_resource, get_remote_file_content
from .env_config_dir import get_env_config_dir

LOGGER = logging.getLogger(__name__)

CURRENT_DIR = as_path(os.path.dirname(__file__))
hosts_to_install = []
sources_list_installed = []


@composite_installer
def veil_hosts_resource(veil_env_name):
    resources = []
    hosts = list_veil_hosts(veil_env_name)
    for host in hosts:
        # user and port are required as setting host_string would not set them accordingly
        if is_initialized_for_another_same_base_instance(host):
            raise Exception('Can not deploy {} on host {} as it is initialized for another same-base instance!!!'.format(host.VEIL_ENV.name, host.name))
        if host.base_name not in hosts_to_install:
            resources.extend([
                veil_host_onetime_config_resource(host=host),
                veil_host_config_resource(host=host),
                veil_host_application_config_resource(host=host),
                veil_host_codebase_resource(host=host)
            ])
            host_users_dir = get_env_config_dir() / 'hosts' / host.base_name / 'USERS'
            if host_users_dir.exists():
                print(cyan('Install Veil host users resource'))
                for user_dir in host_users_dir.dirs():
                    resources.append(veil_host_user_resource(host=host, user_dir=user_dir))
            if any(h.with_user_editor for h in hosts if h.base_name == host.base_name):
                print(cyan('Install Veil host user editor resource'))
                resources.append(veil_host_user_editor_additional_resource(host=host))
            resources.append(veil_host_iptables_rules_resource(host=host))
            hosts_to_install.append(host.base_name)
        for server in host.server_list:
            resources.extend([
                veil_host_directory_resource(host=host, remote_path=server.etc_dir, owner=host.ssh_user, owner_group=host.ssh_user_group),
                veil_host_directory_resource(host=host, remote_path=server.log_dir, owner=host.ssh_user, owner_group=host.ssh_user_group),
                veil_container_resource(host=host, server=server)
            ])
    return resources


@composite_installer
def veil_hosts_codebase_resource(veil_env_name):
    resources = []
    for host in unique(list_veil_hosts(veil_env_name), id_func=lambda h: h.base_name):
        resources.append(veil_host_codebase_resource(host=host))
    return resources


def render_iptables_rules_installer_file(host):
    resources = []
    ssh_ports = set()
    for h in list_veil_hosts(host.VEIL_ENV.name):
        if h.base_name != host.base_name:
            continue
        resources.append(iptables_rule_resource(table='filter', rule='INPUT -p tcp -d {} -m tcp --dport 8443 -j ACCEPT'.format(h.internal_ip)))
        resources.append(iptables_rule_resource(table='nat', rule='POSTROUTING -s {}.0/24 ! -d {}.0/24 -j MASQUERADE'.format(h.lan_range, h.lan_range)))
        resources.extend(h.iptables_rule_resources)
        ssh_ports.add(host.ssh_port)
    resources.extend(list_iptables_resources_to_secure_host(ssh_ports))
    return '\n'.join(to_resource_code(resource) for resource in resources)


@atomic_installer
def veil_host_iptables_rules_resource(host):
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        remote_installer_file_content = get_remote_file_content(host.installed_iptables_rules_installer_path)
        installer_file_content = render_iptables_rules_installer_file(host)
        if remote_installer_file_content:
            action = None if installer_file_content == remote_installer_file_content else 'UPDATE'
        else:
            action = 'INSTALL'
        dry_run_result = get_dry_run_result()
        if dry_run_result is not None:
            key = 'veil_host_iptables_rules?{}'.format(host.VEIL_ENV.name)
            dry_run_result[key] = action or '-'
            return
        if not action:
            return
        with contextlib.closing(StringIO(installer_file_content)) as f:
            fabric.api.put(f, host.iptables_rules_installer_path, use_sudo=True, mode=0600)
        with fabric.api.cd(host.veil_home):
            fabric.api.sudo('veil :{} install veil_installer.installer_resource?{}'.format(host.VEIL_ENV.name, host.iptables_rules_installer_path))
            fabric.api.sudo('iptables-save -c > /etc/iptables.rules')
        fabric.api.sudo('mv -f {} {}'.format(host.iptables_rules_installer_path, host.installed_iptables_rules_installer_path))


@composite_installer
def veil_host_onetime_config_resource(host):
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        initialized = fabric.contrib.files.exists(host.initialized_tag_link)
        if initialized:
            return []

    resources = [
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablesload', host=host, remote_path='/usr/local/bin/iptablesload', owner='root', owner_group='root',
                                mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'iptablessave', host=host, remote_path='/usr/local/bin/iptablessave', owner='root', owner_group='root',
                                mode=0755),
        veil_host_file_resource(local_path=CURRENT_DIR / 'persist-iptables.service', host=host, remote_path='/lib/systemd/system/persist-iptables.service',
                                owner='root', owner_group='root', mode=0755,
                                cmd='systemctl daemon-reload && systemctl enable persist-iptables.service && systemctl start persist-iptables.service'),
        veil_host_file_resource(local_path=CURRENT_DIR / 'sudoers.d.ssh-auth-sock', host=host, remote_path='/etc/sudoers.d/ssh-auth-sock', owner='root',
                                owner_group='root', mode=0440),
        veil_host_file_resource(local_path=CURRENT_DIR / 'ipv4-ip-forward.conf', host=host, remote_path='/etc/sysctl.d/60-lxc-ipv4-ip-forward.conf',
                                owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-lxc-ipv4-ip-forward.conf'),
        veil_host_file_resource(local_path=CURRENT_DIR / 'disable-ipv6.conf', host=host, remote_path='/etc/sysctl.d/60-disable-ipv6.conf',
                                owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-disable-ipv6.conf'),
        veil_host_sources_list_resource(host=host),
        veil_host_init_resource(host=host)  # should be the last one of veil_host_onetime_config_resource which marks the host-initialization tag
    ]
    return resources


@composite_installer
def veil_host_config_resource(host):
    resources = [
        veil_host_directory_resource(host=host, remote_path='/home/{}/.ssh'.format(host.ssh_user), owner=host.ssh_user, owner_group=host.ssh_user_group,
                                     mode=0700),
        veil_host_file_resource(local_path=get_env_config_dir() / '.ssh' / 'authorized_keys', host=host,
                                remote_path='/home/{}/.ssh/authorized_keys'.format(host.ssh_user), owner=host.ssh_user, owner_group=host.ssh_user_group,
                                mode=0600),
        veil_host_file_resource(local_path=CURRENT_DIR / 'apt-config', host=host, remote_path='/etc/apt/apt.conf.d/99-veil-apt-config', owner='root',
                                owner_group='root', mode=0644),
        veil_host_sources_list_resource(host=host)
    ]

    servers = list_veil_servers(host.VEIL_ENV.name)
    if any(s.var_dir for s in servers):
        resources.extend([
            veil_host_directory_resource(host=host, remote_path=host.var_dir, owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0755),
        ])
    if any(s.buckets_dir for s in servers):
        resources.extend([
            veil_host_directory_resource(host=host, remote_path=host.buckets_dir, owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0755),
            veil_host_directory_resource(host=host, remote_path=host.bucket_log_dir, owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0755),
        ])
    if any(s.data_dir for s in servers):
        resources.extend([
            veil_host_directory_resource(host=host, remote_path=host.data_dir, owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0755),
        ])
    if any(s.barman_dir for s in servers):
        resources.extend([
            veil_host_directory_resource(host=host, remote_path=host.barman_dir, owner=host.ssh_user, owner_group=host.ssh_user_group, mode=0755),
        ])
    if any(s.is_guard for s in servers):
        resources.extend([
            veil_host_file_resource(local_path=CURRENT_DIR / 'max-user-watches.conf', host=host, remote_path='/etc/sysctl.d/60-max-user-watches.conf',
                                    owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-max-user-watches.conf'),
        ])
    if any(s.is_monitor for s in servers):
        resources.append(
            veil_host_file_resource(local_path=CURRENT_DIR / 'max-map-count.conf', host=host, remote_path='/etc/sysctl.d/60-max-map-count.conf',
                                    owner='root', owner_group='root', mode=0644, cmd='sysctl -p /etc/sysctl.d/60-max-map-count.conf'),
        )
    return resources


@composite_installer
def veil_host_application_config_resource(host):
    if not (get_env_config_dir() / '.config').exists():
        return []
    return [
        veil_host_file_resource(local_path=get_env_config_dir() / '.config', host=host, remote_path=host.code_dir / '.config', owner=host.ssh_user,
                                owner_group=host.ssh_user_group, mode=0600)
    ]


@atomic_installer
def veil_host_codebase_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_codebase?{}'.format(host.VEIL_ENV.name)
        dry_run_result[key] = 'INSTALL'
        return
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port, forward_agent=True):
        clone_application(host)
        pull_application(host)
        framework_branch = read_veil_framework_branch(host)
        clone_framework(host, framework_branch)
        pull_framework(host, framework_branch)
        init_application(host)


def clone_application(host):
    if fabric.contrib.files.exists(host.veil_home):
        return
    codebase = get_application_codebase()
    codebase_host = codebase.split(':', 1)[0].split('@', 1)[1]
    fabric.api.run('ssh-keyscan {} >> ~/.ssh/known_hosts'.format(codebase_host))
    fabric.api.run('git clone -b {} --depth=1 {} {}'.format(host.veil_application_branch, codebase, host.veil_home))


def clone_framework(host, branch):
    if fabric.contrib.files.exists(host.veil_framework_home):
        return
    fabric.api.run('git clone -b {} --depth=1 --no-single-branch {} {}'.format(branch, get_veil_framework_codebase(), host.veil_framework_home))


def pull_application(host):
    with fabric.api.cd(host.veil_home):
        check_no_changes(host.veil_home)
        while True:
            try:
                fabric.api.run('git pull')
            except Exception:
                sleep(1)
                continue
            else:
                break


def pull_framework(host, branch):
    with fabric.api.cd(host.veil_framework_home):
        fabric.api.run('git checkout {}'.format(branch))
        check_no_changes(host.veil_framework_home)
        while True:
            try:
                fabric.api.run('git pull')
            except Exception:
                sleep(1)
                continue
            else:
                break


def check_no_changes(cwd):
    has_changes_not_committed = bool(fabric.api.run('git diff HEAD', warn_only=True, pty=False))
    if not has_changes_not_committed:
        has_commits_not_pushed = 'Your branch is ahead of' in fabric.api.run('git status', warn_only=True)
    if has_changes_not_committed or has_commits_not_pushed:
        raise Exception('Local changes detected in {} !!!'.format(cwd))


def read_veil_framework_branch(host):
    content = get_remote_file_content(host.veil_home / 'VEIL-BRANCH')
    if not content:
        return 'master'
    for line in content.splitlines():
        if '=' not in line:
            continue
        env_base_name, branch = [x.strip() for x in line.split('=', 1)]
        if env_base_name == host.VEIL_ENV.base_name:
            return branch
    return 'master'


def init_application(host):
    with fabric.api.cd(host.veil_home):
        fabric.api.run('{}/bin/veil :{} init'.format(host.veil_framework_home, host.VEIL_ENV.name))


@atomic_installer
def veil_host_init_resource(host):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_init?{}'.format(host.VEIL_ENV.name)
        dry_run_result[key] = 'INSTALL'
        return
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        fabric.contrib.files.append('/etc/ssh/sshd_config', host.sshd_config or ['PasswordAuthentication no', 'PermitRootLogin no'], use_sudo=True)
        fabric.api.sudo('systemctl reload-or-restart ssh')

        fabric.api.sudo('apt update')
        fabric.api.sudo('apt -y upgrade')
        required_packages = ['unattended-upgrades', 'update-notifier-common', 'iptables', 'git', 'language-pack-en', 'unzip', 'wget', 'python', 'python-dev',
                             'python-pip', 'python-virtualenv']
        fabric.api.sudo('apt -y install {}'.format(' '.join(required_packages)))

        fabric.api.sudo('timedatectl set-timezone {}'.format(host.timezone))

        # enables and starts the systemd-timesyncd.service for time sync on lxc hosts, and which is shared among lxc guests
        fabric.api.sudo('timedatectl set-ntp true')

        with fabric.api.settings(sudo_prefix="sudo -H -S -p '%(sudo_prompt)s' "):
            # upgrade before initializing veil app (veil init) which will create virtualenv and copy pip&wheel into virtual env.
            pip_index_args = '-i {}'.format(host.pypi_index_url) if host.pypi_index_url else ''
            fabric.api.sudo('pip install {} --upgrade "pip>=9.0.1"'.format(pip_index_args))
            fabric.api.sudo('pip install {} --upgrade "setuptools>=34.2.0"'.format(pip_index_args))
            fabric.api.sudo('pip install {} --upgrade "wheel>=0.30.0a0"'.format(pip_index_args))
            fabric.api.sudo('pip install {} --upgrade "virtualenv>=15.1.0"'.format(pip_index_args))

        init_veil_host_lxd(host)

        init_veil_host_basic_layout(host)

        fabric.api.run('touch {}'.format(host.initialized_tag_path))
        if host.initialized_tag_path != host.initialized_tag_link:
            fabric.api.run('ln -s {} {}'.format(host.initialized_tag_path, host.initialized_tag_link))


def init_veil_host_lxd(host):
    init_lxd_daemon()
    init_lxd_user_mapping()
    client = LXDClient(endpoint=host.lxd_endpoint, config_dir=get_env_config_dir())
    init_lxd_profile_resource(client)
    init_lxd_image(client)


def init_lxd_daemon():
    config_file = as_path(get_env_config_dir()) / '.config'
    config = load_config_from(config_file, 'lxd_trusted_password')
    fabric.api.run('lxd init --auto --network-address=[::] --trust-password={}'.format(config.lxd_trusted_password))


def init_lxd_user_mapping():
    ret = fabric.api.run('grep -rl lxd:$UID:1 /etc/subuid', warn_only=True)
    if ret.return_code == 1:
        lxd_user_mapping = fabric.api.run('echo lxd:$UID:1')
        fabric.api.sudo('echo {} >> /etc/subuid'.format(lxd_user_mapping))
    ret = fabric.api.run('grep -rl lxd:$(id -g):1 /etc/subgid', warn_only=True)
    if ret.return_code == 1:
        lxd_group_mapping = fabric.api.run('echo lxd:$(id -g):1')
        fabric.api.sudo('echo {} >> /etc/subgid'.format(lxd_group_mapping))

    ret = fabric.api.run('grep -rl root:$UID:1 /etc/subuid', warn_only=True)
    if ret.return_code == 1:
        lxd_user_mapping = fabric.api.run('echo root:$UID:1')
        fabric.api.sudo('echo {} >> /etc/subuid'.format(lxd_user_mapping))
    ret = fabric.api.run('grep -rl root:$(id -g):1 /etc/subgid', warn_only=True)
    if ret.return_code == 1:
        lxd_group_mapping = fabric.api.run('echo root:$(id -g):1')
        fabric.api.sudo('echo {} >> /etc/subgid'.format(lxd_group_mapping))


def init_lxd_profile_resource(client):
    if client.is_profile_exists(LXD_PROFILE_NAME):
        return
    client.create_profile(LXD_PROFILE_NAME, config={}, devices={
        'root': {
            'path': '/',
            'pool': 'default',
            'type': 'disk'
        },
        'eth0': {
            'name': 'eth0',
            'type': 'nic',
            'nictype': 'bridged',
            'parent': LXD_BRIDGE_NAME
        }
    })


def init_lxd_image(client):
    codename = fabric.api.run('lsb_release -cs', pty=False)
    if client.is_image_exists(codename):
        return
    fabric.api.run('lxc image copy ubuntu:{codename} local: --alias {codename}'.format(codename=codename))


def init_veil_host_basic_layout(host):
    dirs = [host.share_dir, DEPENDENCY_DIR, DEPENDENCY_INSTALL_DIR, PYPI_ARCHIVE_DIR, host.env_dir, host.code_dir, host.etc_dir, host.log_dir]
    fabric.api.sudo('mkdir -p -m 0755 {}'.format(' '.join(dirs)))
    fabric.api.sudo('chown -R {}:{} {}'.format(host.ssh_user, host.ssh_user_group, ' '.join(dirs)))
    if host.VEIL_ENV.name != host.VEIL_ENV.base_name:
        env_full_name_link = host.env_dir.parent / host.VEIL_ENV.name
        fabric.api.sudo('ln -sfT {} {}'.format(host.env_dir, env_full_name_link))
        fabric.api.sudo('chown -h {}:{} {}'.format(host.ssh_user, host.ssh_user_group, env_full_name_link))


def is_initialized_for_another_same_base_instance(host):
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        return host.initialized_tag_link != host.initialized_tag_path \
               and fabric.contrib.files.exists(host.initialized_tag_link) \
               and not fabric.contrib.files.exists(host.initialized_tag_path)


@atomic_installer
def veil_host_sources_list_resource(host):
    if host.base_name in sources_list_installed:
        return

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_sources_list?{}'.format(host.VEIL_ENV.name)
        dry_run_result[key] = 'INSTALL'
        return
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        sources_list_path = '/etc/apt/sources.list'
        context = dict(mirror=host.apt_url, codename=fabric.api.run('lsb_release -cs', pty=False))
        fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=sources_list_path))
        fabric.contrib.files.upload_template('sources.list.j2', sources_list_path, context=context, use_jinja=True, template_dir=CURRENT_DIR, use_sudo=True,
                                             backup=False, mode=0644)
        fabric.api.sudo('chown root:root {}'.format(sources_list_path))

    sources_list_installed.append(host.base_name)


@atomic_installer
def veil_host_directory_resource(host, remote_path, owner='root', owner_group='root', mode=0755):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_directory?{}&path={}'.format(host.VEIL_ENV.name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        fabric.api.sudo('mkdir -p {}'.format(remote_path))
        fabric.api.sudo('chmod {:o} {}'.format(mode, remote_path))
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))


@atomic_installer
def veil_host_file_resource(local_path, host, remote_path, owner, owner_group, mode, keep_origin=False, cmd=None):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'veil_host_file?{}&path={}'.format(host.VEIL_ENV.name, remote_path)
        dry_run_result[key] = 'INSTALL'
        return
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        if keep_origin:
            fabric.api.sudo('cp -pn {path} {path}.origin'.format(path=remote_path))
        fabric.api.put(local_path, remote_path, use_sudo=True, mode=mode)
        fabric.api.sudo('chown {}:{} {}'.format(owner, owner_group, remote_path))
        if cmd:
            fabric.api.sudo(cmd)


@atomic_installer
def veil_host_user_resource(host, user_dir):
    username = user_dir.basename()
    initialized_file_path = '/home/{}/.veil_host_user_initialized'.format(username)
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        installed = fabric.contrib.files.exists(initialized_file_path, use_sudo=True)
        dry_run_result = get_dry_run_result()
        if dry_run_result is not None:
            key = 'veil_host_user_{}?{}'.format(username, host.VEIL_ENV.name)
            dry_run_result[key] = '-' if installed else 'INSTALL'
            return

        if not installed:
            ret = fabric.api.run('getent passwd {}'.format(username), warn_only=True)
            if ret.failed:
                uid = (user_dir / 'id').text().strip()
                fabric.api.sudo('adduser --uid {uid} {username} --gecos {username} --disabled-login --shell /usr/sbin/nologin --quiet'.format(username=username, uid=uid))
        fabric.api.put(local_path=user_dir, remote_path='/home/', use_sudo=True, mode=0755)
        fabric.api.sudo('chown -R {username}:{username} /home/{username}/'.format(username=username))
        user_ssh_dir = user_dir / '.ssh'
        if user_ssh_dir.isdir():
            fabric.api.sudo('chmod 0700 /home/{}/.ssh'.format(username), user=username)
            if user_ssh_dir.listdir():
                fabric.api.sudo('chmod 0600 /home/{}/.ssh/*'.format(username), user=username)
        for f in as_path(user_dir):
            if f.endswith('.service'):
                fabric.api.put(local_path=f, remote_path='/lib/systemd/system/', use_sudo=True, mode=0644)
                fabric.api.sudo('systemctl daemon-reload')
                service_name = f.basename()
                fabric.api.sudo('systemctl enable {}'.format(service_name))
                fabric.api.sudo('systemctl start {}'.format(service_name))
        if not installed:
            fabric.api.sudo('touch {}'.format(initialized_file_path))
            fabric.api.sudo('chown {}:{} {}'.format(username, username, initialized_file_path))


@atomic_installer
def veil_host_user_editor_additional_resource(host):
    with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
        installed = fabric.contrib.files.contains('/etc/ssh/sshd_config', 'Match User editor')
        dry_run_result = get_dry_run_result()
        if dry_run_result is not None:
            key = 'veil_host_user_editor?{}'.format(host.VEIL_ENV.name)
            dry_run_result[key] = '-' if installed else 'INSTALL'
            return

        if not fabric.contrib.files.exists(host.editorial_dir, use_sudo=True):
            # user `editor` creation is done by veil_host_user_resource
            fabric.api.run('mkdir -p -m 0755 {}'.format(host.editorial_dir))
            fabric.api.sudo('chown -R editor:editor {}'.format(host.editorial_dir))

        if installed:
            return

        # do not add any config after Match User unless you know what you write
        fabric.contrib.files.append('/etc/ssh/sshd_config',
                                    ['Match User editor', 'ChrootDirectory {}'.format(host.editorial_dir.parent),
                                     'ForceCommand internal-sftp'], use_sudo=True)
        fabric.api.sudo('systemctl reload-or-restart ssh.service')
