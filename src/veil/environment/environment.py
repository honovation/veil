# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import getpass
import itertools
import operator
import os
import re

from veil_component import *

DEFAULT_DNS_SERVERS = ('119.29.29.29', '182.254.116.116', '8.8.8.8', '8.8.4.4')

DEPENDENCY_URL = 'http://dependency-veil.qiniudn.com'
DEPENDENCY_SSL_URL = 'https://dependency-veil.qiniudn.com'
APT_URL = 'https://mirrors.aliyun.com/ubuntu/'
PYPI_INDEX_URL = 'https://pypi.doubanio.com/simple/'

OPT_DIR = as_path('/opt')
SHARE_DIR = OPT_DIR / 'share'
DEPENDENCY_DIR = SHARE_DIR / 'dependency'
DEPENDENCY_INSTALL_DIR = SHARE_DIR / 'dependency-install'
PYPI_ARCHIVE_DIR = SHARE_DIR / 'pypi'

VEIL_ENV_DIR = (VEIL_HOME if VEIL_ENV.is_dev or VEIL_ENV.is_test else OPT_DIR) / VEIL_ENV.base_name
VEIL_ETC_DIR = VEIL_ENV_DIR / 'etc' / VEIL_SERVER_NAME
VEIL_LOG_DIR = VEIL_ENV_DIR / 'log' / VEIL_SERVER_NAME
VEIL_VAR_DIR = VEIL_ENV_DIR / 'var'
VEIL_EDITORIAL_DIR = VEIL_VAR_DIR / 'editor-rootfs' / 'editorial'
VEIL_BUCKETS_DIR = VEIL_VAR_DIR / 'buckets'
VEIL_DATA_DIR = VEIL_VAR_DIR / 'data'
VEIL_BARMAN_DIR = VEIL_VAR_DIR / 'barman'

VEIL_BUCKET_LOG_DIR = VEIL_BUCKETS_DIR / 'log'
VEIL_BUCKET_INLINE_STATIC_FILES_DIR = VEIL_BUCKETS_DIR / 'inline-static-files'
VEIL_BUCKET_CAPTCHA_IMAGE_DIR = VEIL_BUCKETS_DIR / 'captcha-image'
VEIL_BUCKET_UPLOADED_FILES_DIR = VEIL_BUCKETS_DIR / 'uploaded-files'

VEIL_BACKUP_ROOT = as_path('/backup')
VEIL_BACKUP_MIRROR_ROOT = as_path('~/backup_mirror')

CURRENT_USER = os.getenv('SUDO_USER') or getpass.getuser()
CURRENT_USER_GROUP = CURRENT_USER

SECURITY_CONFIG_FILE = (VEIL_HOME if VEIL_ENV.is_dev or VEIL_ENV.is_test else VEIL_HOME.parent) / '.config'

if VEIL_ENV.is_dev or VEIL_ENV.is_test:
    from veil.server.os import directory_resource
    BASIC_LAYOUT_RESOURCES = [
            directory_resource(path=VEIL_ENV_DIR),
            directory_resource(path=VEIL_ETC_DIR.parent),
            directory_resource(path=VEIL_ETC_DIR),
            directory_resource(path=VEIL_LOG_DIR.parent),
            directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
            directory_resource(path=VEIL_VAR_DIR),
            directory_resource(path=VEIL_BUCKETS_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
            directory_resource(path=VEIL_BUCKET_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
            directory_resource(path=VEIL_DATA_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
            directory_resource(path=VEIL_BARMAN_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        ]
elif VEIL_ENV.name != VEIL_ENV.base_name:
    from veil.server.os import symbolic_link_resource
    BASIC_LAYOUT_RESOURCES = [symbolic_link_resource(path=VEIL_ENV_DIR.parent / VEIL_ENV.name, to=VEIL_ENV_DIR)]
else:
    BASIC_LAYOUT_RESOURCES = []


NAME_PATTERN = re.compile(r'^[a-zA-Z0-9-]+$')


def veil_env(name, hosts, servers, sorted_server_names=None, apt_url=APT_URL, pypi_index_url=PYPI_INDEX_URL, deployment_memo=None, config=None):
    """
    Veil env. consists of multiple veil servers deployed on one or more veil hosts, every veil server is running as an LXD container.
    Recommended deployment of a Veil Env. consists of two hosts:
        Host #1: runs veil servers such as guard, web, db, worker
        Host #2: runs veil servers such as guard, barman, monitor
    If only one host available, it is okay to deploy the whole veil env. on one host.

    Server guard:
        1. Periodically: makes host backup (except PostgreSQL) and synchronizes to backup mirror
        2. Near-real-time: synchronizes latest updates for buckets and redis aof files to backup-mirror
    Every host requiring bucket&redis backup should run a guard server.
    At most one guard server is allowed for hosts with the same base name.

    Backup mirror is a special host configured on every guard server to mirror the backups on another host.
    Every guard server should have one backup mirror.
    At most one backup mirror is allowed in one env.

    At most one barman server is available for PostgreSQL server backup (PITR with streaming replication).
    At most one monitor server is allowed in one env.
    """
    server_names = servers.keys()
    if sorted_server_names:
        assert set(sorted_server_names) == set(server_names), \
            'ENV {}: inconsistency between sorted_server_names {} and server_names {}'.format(name, sorted_server_names, server_names)
        assert 'monitor' not in sorted_server_names or 'monitor' == sorted_server_names[-1], \
            'ENV {}: monitor should be the last one in {}'.format(name, sorted_server_names)
    else:
        sorted_server_names = sorted(server_names)

    from veil.model.collection import objectify

    assert NAME_PATTERN.match(name) is not None, 'invalid characters in veil environment name: {}'.format(name)
    env = objectify({
        'name': name, 'hosts': hosts, 'servers': servers, 'sorted_server_names': sorted_server_names,
        'apt_url': apt_url,
        'pypi_index_url': pypi_index_url,
        'deployment_memo': deployment_memo, 'config': config or {}
    })
    env.VEIL_ENV = VeilEnv(env.name)
    env.env_dir = OPT_DIR / env.VEIL_ENV.base_name
    env.veil_home = VEIL_HOME if env.VEIL_ENV.is_dev or env.VEIL_ENV.is_test else env.env_dir / 'code' / 'app'
    env.server_list = []
    env.backup_mirror = next((server.backup_mirror for server in env.servers.values() if server.backup_mirror), None)
    for server_name, server in env.servers.items():
        assert NAME_PATTERN.match(server_name) is not None, 'invalid characters in veil server name: {}'.format(server_name)
        server.VEIL_ENV = env.VEIL_ENV
        server.is_guard = is_guard_server(server_name)
        server.is_barman = is_barman_server(server_name)
        server.is_monitor = is_monitor_server(server_name)
        server.name = server_name
        server.fullname = '{}/{}'.format(server.VEIL_ENV.name, server.name)
        server.start_order = 1000 + 10 * sorted_server_names.index(server.name) if sorted_server_names else 0
        server.apt_url = env.apt_url
        server.pypi_index_url = env.pypi_index_url
        server.veil_home = env.veil_home
        server.code_dir = server.veil_home.parent
        server.veil_framework_home = server.code_dir / 'veil'
        server.container_name = '{}---{}'.format(server.VEIL_ENV.name, server.name)
        server.container_installer_path = SHARE_DIR / 'veil-container-INSTALLER-{}'.format(server.container_name)
        server.installed_container_installer_path = '{}.installed'.format(server.container_installer_path)
        server.container_initialized_tag_path = SHARE_DIR / 'veil-container-{}.initialized'.format(server.container_name)
        server.deployed_tag_path = SHARE_DIR / 'veil-server-{}.deployed'.format(server.container_name)
        server.patched_tag_path = SHARE_DIR / 'veil-server-{}.patched'.format(server.container_name)
        server.host = None
        env.server_list.append(server)
    env.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))
    for host_name, host in env.hosts.items():
        assert NAME_PATTERN.match(host_name) is not None, 'invalid characters in veil host name: {}'.format(host_name)
        host.VEIL_ENV = env.VEIL_ENV
        host.name = host_name
        # host base_name can be used to determine host config dir: as_path('{}/{}/hosts/{}'.format(config_dir, host.VEIL_ENV.name, host.base_name))
        # 生产环境部署到多个host，staging只有一台host，用一台host模拟多台host时，在staging的host name加--1,--2,--3表示多台机器
        host.base_name = host.name.rsplit('--', 1)[0]
        host.apt_url = env.apt_url
        host.pypi_index_url = env.pypi_index_url
        host.ssh_user_home = as_path('/home') / host.ssh_user
        host.share_dir = SHARE_DIR
        host.env_dir = env.env_dir
        host.etc_dir = host.env_dir / 'etc'
        host.log_dir = host.env_dir / 'log'
        host.var_dir = host.env_dir / 'var'
        host.editorial_dir = host.var_dir / 'editor-rootfs' / 'editorial'
        host.buckets_dir = host.var_dir / 'buckets'
        host.bucket_log_dir = host.buckets_dir / 'log'
        host.data_dir = host.var_dir / 'data'
        host.barman_dir = host.var_dir / 'barman'
        host.veil_home = env.veil_home
        host.veil_application_branch = 'env-{}'.format(host.VEIL_ENV.name)
        host.code_dir = host.veil_home.parent
        host.veil_framework_home = host.code_dir / 'veil'
        host.iptables_rules_installer_path = SHARE_DIR / 'veil-host-iptables-rules-INSTALLER-{}'.format(host.VEIL_ENV.name)
        host.installed_iptables_rules_installer_path = '{}.installed'.format(host.iptables_rules_installer_path)
        host.initialized_tag_path = SHARE_DIR / 'veil-host-{}.initialized'.format(host.VEIL_ENV.name)
        host.initialized_tag_link = SHARE_DIR / 'veil-host-{}.initialized'.format(host.VEIL_ENV.base_name)
        host.rollbackable_tag_path = SHARE_DIR / 'veil-host-{}.rollbackable'.format(host.VEIL_ENV.name)
        host.with_user_editor = False
        host.server_list = []
        for server_name, server in env.servers.items():
            if host.name != server.host_name:
                continue
            server.host = host
            server.lxd_endpoint = host.lxd_endpoint
            server.host_base_name = host.base_name
            server.ssh_user = host.ssh_user
            server.ssh_port = host.ssh_port
            server.ssh_user_group = host.ssh_user_group
            server.internal_ip = '{}.{}'.format(host.lan_range, server.sequence_no)
            server.deploys_via = '{}@{}:{}'.format(server.ssh_user, server.internal_ip, server.ssh_port)
            server.env_dir = host.env_dir
            server.etc_dir = host.etc_dir / server.name
            server.log_dir = host.log_dir / server.name
            if server.mount_var_dir or server.mount_editorial_dir or server.mount_buckets_dir or server.mount_data_dir or server.mount_barman_dir:
                server.var_dir = host.var_dir
            else:
                server.var_dir = None
            server.editorial_dir = host.editorial_dir if server.mount_editorial_dir else None
            server.buckets_dir = host.buckets_dir if server.mount_buckets_dir else None
            server.data_dir = host.data_dir if server.mount_data_dir else None
            server.barman_dir = host.barman_dir if server.mount_barman_dir else None
            host.with_user_editor = host.with_user_editor or server.mount_editorial_dir
            host.server_list.append(server)
        host.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))

    if env.hosts:
        assert all(host.server_list for host in env.hosts.values()), 'ENV {}: found host without server(s)'.format(env.name)
        assert all(server.host for server in env.servers.values()), 'ENV {}: found server without host'.format(env.name)
        assert all(len(host.server_list) == len(set(server.sequence_no for server in host.server_list)) for host in
                   env.hosts.values()), 'ENV {}: found sequence no conflict among servers on one host'.format(env.name)
        assert all(len([server for server in servers if server.is_guard]) <= 1 for _, servers
                   in itertools.groupby(sorted(env.servers.values(), key=operator.attrgetter('host_base_name')), operator.attrgetter('host_base_name'))
                   ), 'ENV {}: found more than one guard on one host'.format(env.name)
        assert len([server for server in env.servers.values() if server.is_barman]) <= 1, 'ENV {}: found more than one barman'.format(env.name)
        assert len([server for server in env.servers.values() if server.is_monitor]) <= 1, 'ENV {}: found more than one monitor'.format(env.name)
        assert all(not server.is_guard or server.mount_var_dir for server in env.servers.values()), 'ENV {}: found guard without var mount'.format(env.name)
        assert all(not server.is_barman or server.mount_barman_dir for server in env.servers.values()), \
            'ENV {}: found barman without barman mount'.format(env.name)
        assert all(server.is_guard or not server.mount_var_dir for server in env.servers.values()), \
            'ENV {}: found servers not guard with var mount'.format(env.name)
        assert all(
            not server.is_monitor or not server.mount_var_dir and not server.mount_editorial_dir and not server.mount_buckets_dir and not server.mount_data_dir and not server.mount_barman_dir
            for server in env.servers.values()), 'ENV {}: found monitor with var/editorial/buckets/data mount'.format(env.name)

        assert all(
            (server.is_guard or server.is_barman) and server.backup_mirror or not (server.is_guard or server.is_barman) and not server.backup_mirror for server
            in env.servers.values()), 'ENV {}: found guard/barman without backup mirror or non-guard/barman server with backup mirror'.format(env.name)
        assert all(not server.backup_mirror or env.backup_mirror == server.backup_mirror for server in env.servers.values()), \
            'ENV {}: found more than one backup mirror, at most one is allowed in one env.'.format(env.name)

    # break cyclic reference between host and server to get freeze_dict_object out of complain
    for server in env.servers.values():
        del server.host

    return env


def veil_host(lan_range, external_ip, ssh_port=22, ssh_user='dejavu', sshd_config=(), iptables_rule_resources=(), timezone=None, external_service_ports=(),
              lxd_endpoint=None):
    if sshd_config and 'PasswordAuthentication no' not in sshd_config:
        raise AssertionError('password authentication should not be allowed on host')
    if sshd_config and 'PermitRootLogin no' not in sshd_config:
        raise AssertionError('root login should not be allowed on host')

    from veil.model.collection import objectify
    internal_ip = '{}.1'.format(lan_range)
    return objectify({
        'timezone': timezone or get_application_timezone(),
        'lan_range': lan_range,
        'internal_ip': internal_ip,
        'external_ip': external_ip,
        'ssh_port': ssh_port,
        'ssh_user': ssh_user,
        'ssh_user_group': ssh_user,
        'sshd_config': sshd_config,
        'iptables_rule_resources': iptables_rule_resources,
        'deploys_via': '{}@{}:{}'.format(ssh_user, internal_ip, ssh_port),
        'external_service_ports': external_service_ports,
        'lxd_endpoint': lxd_endpoint or 'https://{}.1:8443'.format(lan_range)
    })


def veil_server(host_name, sequence_no, programs, resources=(), supervisor_http_host=None, supervisor_http_port=None,
                name_servers=None, backup_mirror=None, mount_var_dir=False, mount_editorial_dir=False, mount_buckets_dir=False,
                mount_data_dir=False, mount_barman_dir=False, memory_limit=None, cpu_share=None, cpus=None):
    assert not mount_var_dir or not mount_editorial_dir and not mount_buckets_dir and not mount_data_dir and not mount_barman_dir

    from veil.model.collection import objectify
    if backup_mirror:
        backup_mirror = objectify(backup_mirror)
        backup_mirror.deploys_via = '{}@{}:{}'.format(backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror.ssh_port)
    return objectify({
        'host_name': host_name,
        'sequence_no': sequence_no,
        'programs': programs,
        'resources': resources,
        'supervisor_http_host': supervisor_http_host,
        'supervisor_http_port': supervisor_http_port,
        'name_servers': name_servers or DEFAULT_DNS_SERVERS,
        'backup_mirror': backup_mirror,
        'mount_var_dir': mount_var_dir,
        'mount_editorial_dir': mount_editorial_dir,
        'mount_buckets_dir': mount_buckets_dir,
        'mount_data_dir': mount_data_dir,
        'mount_barman_dir': mount_barman_dir,
        'memory_limit': memory_limit,
        'cpu_share': cpu_share,
        'cpus': cpus
    })


def is_guard_server(name):
    return 'guard' == name.split('-', 1)[0]


def is_barman_server(name):
    return 'barman' == name


def is_monitor_server(name):
    return 'monitor' == name


def list_veil_servers(veil_env_name, include_guard_server=True, include_monitor_server=True, include_barman_server=True):
    return [s for s in get_veil_env(veil_env_name).server_list if
            (include_guard_server or not s.is_guard) and (include_monitor_server or not s.is_monitor) and (include_barman_server or not s.is_barman)]


def get_veil_server(veil_env_name, veil_server_name):
    return get_veil_env(veil_env_name).servers[veil_server_name]


def get_current_veil_server():
    return get_veil_server(VEIL_ENV.name, VEIL_SERVER_NAME)


def list_veil_hosts(veil_env_name):
    return sorted(get_veil_env(veil_env_name).hosts.values(), key=operator.attrgetter('name'))


def get_veil_host(veil_env_name, veil_host_name):
    return get_veil_env(veil_env_name).hosts[veil_host_name]


def get_veil_env(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name]


def get_current_veil_env():
    return get_veil_env(VEIL_ENV.name)


def get_veil_env_deployment_memo(veil_env_name):
    return get_veil_env(veil_env_name).deployment_memo


def get_application():
    import __veil__

    return __veil__


def get_application_codebase():
    return get_application().CODEBASE


def get_application_timezone():
    return getattr(get_application(), 'TIMEZONE', 'Asia/Shanghai')


def get_application_sms_whitelist():
    return getattr(get_application(), 'SMS_WHITELIST', set())


def get_application_email_whitelist():
    return getattr(get_application(), 'EMAIL_WHITELIST', set())


def get_veil_framework_codebase():
    return get_application().VEIL_FRAMEWORK_CODEBASE


_application_version = None


def get_application_version():
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        return VEIL_ENV.type
    global _application_version
    from veil.utility.shell import shell_execute
    if not _application_version:
        app_commit_hash = shell_execute('git rev-parse HEAD', cwd=VEIL_HOME, capture=True)
        framework_commit_hash = get_veil_framework_version()
        _application_version = '{}-{}'.format(app_commit_hash, framework_commit_hash)
    return _application_version


def get_veil_framework_version():
    from veil.utility.shell import shell_execute
    return shell_execute('git rev-parse HEAD', cwd=VEIL_FRAMEWORK_HOME, capture=True)
