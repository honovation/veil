from __future__ import unicode_literals, print_function, division
import getpass
import os
from veil_component import *
from veil.server.os import *


APT_URL = 'http://mirrors.163.com/ubuntu/'
DEPENDENCY_URL = 'http://dependency-veil.qiniudn.com'
PYPI_INDEX_URL = 'http://pypi.douban.com/simple/' # the official url "https://pypi.python.org/simple/" is blocked

OPT_DIR = as_path('/opt')
SHARE_DIR = OPT_DIR / 'share'
DEPENDENCY_DIR = SHARE_DIR / 'dependency'
DEPENDENCY_INSTALL_DIR = SHARE_DIR / 'dependency-install'
PYPI_ARCHIVE_DIR = SHARE_DIR / 'pypi'

VEIL_ENV_DIR = (VEIL_HOME if VEIL_ENV_TYPE in ('development', 'test') else OPT_DIR) / VEIL_ENV_NAME
VEIL_ETC_DIR = VEIL_ENV_DIR / 'etc' / VEIL_SERVER_NAME
VEIL_VAR_DIR = VEIL_ENV_DIR / 'var'
VEIL_EDITORIAL_DIR = VEIL_VAR_DIR / 'editorial'
VEIL_BUCKETS_DIR = VEIL_VAR_DIR / 'buckets'
VEIL_BUCKET_LOG_DIR = VEIL_BUCKETS_DIR / 'log'
VEIL_DATA_DIR = VEIL_VAR_DIR / 'data'
VEIL_LOG_DIR = VEIL_ENV_DIR / 'log' / VEIL_SERVER_NAME

CURRENT_USER = os.getenv('SUDO_USER') or getpass.getuser()
CURRENT_USER_GROUP = CURRENT_USER
CURRENT_USER_HOME = as_path(os.getenv('HOME'))

BASIC_LAYOUT_RESOURCES = [
    directory_resource(path=VEIL_ENV_DIR),
    directory_resource(path=VEIL_ETC_DIR.parent),
    directory_resource(path=VEIL_ETC_DIR),
    directory_resource(path=VEIL_VAR_DIR),
    directory_resource(path=VEIL_BUCKETS_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
    directory_resource(path=VEIL_BUCKET_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
    directory_resource(path=VEIL_DATA_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
    directory_resource(path=VEIL_LOG_DIR.parent),
    directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
]


def veil_env(name, hosts, servers, sorted_server_names=None, deployment_memo=None):
    server_names = servers.keys()
    if sorted_server_names:
        assert set(sorted_server_names) == set(server_names), 'ENV {}: inconsistency between sorted_server_names {} and server_names {}'.format(
            VEIL_ENV_NAME, sorted_server_names, server_names)
    else:
        sorted_server_names = sorted(server_names)

    from veil.model.collection import objectify
    env = objectify({'name': name, 'hosts': hosts, 'servers': servers, 'sorted_server_names': sorted_server_names, 'deployment_memo': deployment_memo})
    env.env_dir = OPT_DIR / env.name
    env.veil_home = VEIL_HOME if env.name in ('development', 'test') else env.env_dir / 'code' / 'app'
    env.server_list = []
    for server_name, server in env.servers.items():
        server.env_name = env.name
        server.name = server_name
        server.fullname = '{}/{}'.format(server.env_name, server.name)
        server.start_order = 1000 + 10 * sorted_server_names.index(server.name) if sorted_server_names else 0
        server.veil_home = env.veil_home
        server.code_dir = server.veil_home.parent
        server.veil_framework_home = server.code_dir / 'veil'
        server.container_name = '{}-{}'.format(server.env_name, server.name)
        server.container_installer_path = SHARE_DIR / 'veil-container-INSTALLER-{}'.format(server.container_name)
        server.installed_container_installer_path = '{}.installed'.format(server.container_installer_path)
        server.container_initialized_tag_path = SHARE_DIR / 'veil-container-{}.initialized'.format(server.container_name)
        server.deployed_tag_path = SHARE_DIR / 'veil-server-{}.deployed'.format(server.container_name)
        server.patched_tag_path = SHARE_DIR / 'veil-server-{}.patched'.format(server.container_name)
        server.host = None
        env.server_list.append(server)
    env.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))
    for host_name, host in env.hosts.items():
        host.env_name = env.name
        host.name = host_name
        # host base_name can be used to determine host config dir: as_path('{}/{}/hosts/{}'.format(config_dir, host.env_name, host.base_name))
        host.base_name = host.name.split('/', 1)[0]  # e.g. ljhost-005/3 => ljhost-005
        host.opt_dir = OPT_DIR
        host.share_dir = SHARE_DIR
        host.env_dir = env.env_dir
        host.etc_dir = host.env_dir / 'etc'
        host.log_dir = host.env_dir / 'log'
        host.var_dir = host.env_dir / 'var'
        host.editorial_dir = host.var_dir / 'editorial'
        host.buckets_dir = host.var_dir / 'buckets'
        host.data_dir = host.var_dir / 'data'
        host.veil_home = env.veil_home
        host.veil_application_branch = 'env-{}'.format(host.env_name)
        host.code_dir = host.veil_home.parent
        host.veil_framework_home = host.code_dir / 'veil'
        host.initialized_tag_path = SHARE_DIR / 'veil-host-{}.initialized'.format(host.env_name)
        host.server_list = []
        for server_name, server in env.servers.items():
            if host.name != server.host_name:
                continue
            server.host = host
            server.host_base_name = host.base_name
            server.ssh_user = host.ssh_user
            server.ssh_user_group = host.ssh_user_group
            server.deploys_via = server.deploys_via or '{}@{}:{}'.format(host.ssh_user, host.internal_ip, '{}22'.format(server.sequence_no))
            server.etc_dir = host.etc_dir / server.name
            server.log_dir = host.log_dir / server.name
            server.editorial_dir = host.editorial_dir if server.mount_editorial_dir else None
            server.buckets_dir = host.buckets_dir if server.mount_buckets_dir else None
            server.data_dir = host.data_dir if server.mount_data_dir else None
            host.server_list.append(server)
        host.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))

    if env.hosts:
        assert all(host.server_list for host in env.hosts.values()), 'ENV {}: found host without server(s)'.format(VEIL_ENV_NAME)
        assert all(server.host for server in env.servers.values()), 'ENV {}: found server without host'.format(VEIL_ENV_NAME)
        assert all(len(host.server_list) == len(set(server.sequence_no for server in host.server_list)) for host in env.hosts.values()), \
            'ENV {}: found sequence no conflict among servers on one host'.format(VEIL_ENV_NAME)

    # break cyclic reference between host and server to get freeze_dict_object out of complain
    for server in env.servers.values():
        del server.host

    return env


def veil_host(internal_ip, external_ip, ssh_port=22, ssh_user='dejavu', lan_range='10.0.3', lan_interface='lxcbr0', mac_prefix='00:16:3e:73:bb',
        resources=()):
    from veil.model.collection import objectify
    return objectify({
        'internal_ip': internal_ip,
        'external_ip': external_ip,
        'ssh_port': ssh_port,
        'ssh_user': ssh_user,
        'ssh_user_group': ssh_user,
        'lan_range': lan_range,
        'lan_interface': lan_interface,
        'mac_prefix': mac_prefix,
        'resources': resources,
        'deploys_via': '{}@{}:{}'.format(ssh_user, internal_ip, ssh_port)
    })


def veil_server(host_name, sequence_no, programs, deploys_via=None, resources=(), supervisor_http_port=None, name_servers=None, backup_mirror=None,
        mount_editorial_dir=False, mount_buckets_dir=False, mount_data_dir=False, memory_limit=None, cpu_share=None):
    from veil.model.collection import objectify
    if backup_mirror:
        backup_mirror = objectify(backup_mirror)
        backup_mirror.deploys_via = '{}@{}:{}'.format(backup_mirror.ssh_user, backup_mirror.host_ip, backup_mirror.ssh_port)
    return objectify({
        'host_name': host_name,
        'sequence_no': sequence_no,
        'programs': programs,
        'resources': resources,
        'supervisor_http_port': supervisor_http_port,
        'name_servers': name_servers or ['114.114.114.114', '114.114.115.115', '8.8.8.8', '8.8.4.4'],
        'backup_mirror': backup_mirror,
        'mount_editorial_dir': mount_editorial_dir,
        'mount_buckets_dir': mount_buckets_dir,
        'mount_data_dir': mount_data_dir,
        'memory_limit': memory_limit,
        'cpu_share': cpu_share,
        'deploys_via': deploys_via
    })


def list_veil_servers(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].server_list


def get_veil_server(veil_env_name, veil_server_name):
    return get_application().ENVIRONMENTS[veil_env_name].servers[veil_server_name]


def get_current_veil_server():
    return get_veil_server(VEIL_ENV_NAME, VEIL_SERVER_NAME)


def list_veil_hosts(veil_env_name):
    return sorted(get_application().ENVIRONMENTS[veil_env_name].hosts.values(), key=lambda h: h.name)


def get_veil_host(veil_env_name, veil_host_name):
    return get_application().ENVIRONMENTS[veil_env_name].hosts[veil_host_name]


def get_veil_env_deployment_memo(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].deployment_memo


def get_application_codebase():
    return get_application().CODEBASE


def get_application():
    import __veil__

    return __veil__


VEIL_FRAMEWORK_CODEBASE = 'git@ljhost-003.dmright.com:/opt/git/veil.git'


_application_version = None

def get_application_version():
    if VEIL_ENV_TYPE in ('development', 'test'):
        return  VEIL_ENV_TYPE
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
