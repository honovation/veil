from __future__ import unicode_literals, print_function, division
from .environment import APT_URL
from .environment import DEPENDENCY_URL
from .environment import PYPI_INDEX_URL
from .environment import OPT_DIR
from .environment import HOST_SHARE_DIR
from .environment import DEPENDENCY_DIR
from .environment import DEPENDENCY_INSTALL_DIR
from .environment import PYPI_ARCHIVE_DIR
from .environment import VEIL_HOME
from .environment import VEIL_FRAMEWORK_HOME
from .environment import VEIL_FRAMEWORK_CODEBASE
from .environment import VEIL_LOG_DIR
from .environment import VEIL_ETC_DIR
from .environment import VEIL_VAR_DIR
from .environment import VEIL_EDITORIAL_DIR
from .environment import VEIL_BUCKETS_DIR
from .environment import VEIL_DATA_DIR
from .environment import VEIL_ENV_TYPE
from .environment import VEIL_ENV_NAME
from .environment import VEIL_SERVER_NAME
from .environment import CURRENT_OS
from .environment import CURRENT_USER
from .environment import CURRENT_USER_GROUP
from .environment import CURRENT_USER_HOME
from .environment import BASIC_LAYOUT_RESOURCES
from .environment import get_application_version
from .environment import get_veil_framework_version


def veil_env(name, hosts, servers, sorted_server_names=None, deployment_memo=None):
    server_names = servers.keys()
    if sorted_server_names:
        assert set(sorted_server_names) == set(server_names), 'ENV {}: inconsistency between sorted_server_names {} and server_names {}'.format(
            VEIL_ENV_NAME, sorted_server_names, server_names)
    else:
        sorted_server_names = sorted(server_names)

    from veil.model.collection import objectify
    env = objectify({'hosts': hosts, 'servers': servers, 'sorted_server_names': sorted_server_names, 'deployment_memo': deployment_memo})
    env.veil_env_path = veil_env_path(name)
    env.veil_home = veil_home(name)
    env.veil_application_branch = 'env-{}'.format(name)
    env.veil_framework_home = env.veil_home.parent / 'veil'
    env.server_list = []
    for server_name, server in env.servers.items():
        server.env_name = name
        server.name = server_name
        server.fullname = '{}/{}'.format(server.env_name, server.name)
        server.start_order = 1000 + 10 * sorted_server_names.index(server_name) if sorted_server_names else 0
        server.veil_env_path = env.veil_env_path
        server.veil_home = env.veil_home
        server.veil_application_branch = env.veil_application_branch
        server.veil_framework_home = env.veil_framework_home
        server.container_name = '{}-{}'.format(server.env_name, server.name)
        server.container_installer_path = HOST_SHARE_DIR / 'veil-container-INSTALLER-{}'.format(server.container_name)
        server.installed_container_installer_path = '{}.installed'.format(server.container_installer_path)
        server.container_initialized_tag_path = HOST_SHARE_DIR / 'veil-container-{}.initialized'.format(server.container_name)
        server.deployed_tag_path = HOST_SHARE_DIR / 'veil-server-{}.deployed'.format(server.container_name)
        server.patched_tag_path = HOST_SHARE_DIR / 'veil-server-{}.patched'.format(server.container_name)
        server.host = None
        env.server_list.append(server)
    env.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))
    for host_name, host in env.hosts.items():
        host.env_name = name
        host.name = host_name
        # host base_name can be used to determine host config dir: as_path('{}/{}/hosts/{}'.format(config_dir, host.env_name, host.base_name))
        host.base_name = host_name.split('/', 1)[0]  # e.g. ljhost-005/3 => ljhost-005
        host.veil_env_path = env.veil_env_path
        host.veil_home = env.veil_home
        host.veil_application_branch = env.veil_application_branch
        host.veil_framework_home = env.veil_framework_home
        host.initialized_tag_path = HOST_SHARE_DIR / 'veil-host-{}.initialized'.format(host.env_name)
        host.server_list = []
        for server_name, server in env.servers.items():
            if host.name != server.host_name:
                continue
            server.host_base_name = host.base_name
            server.deploys_via = server.deploys_via or '{}@{}:{}'.format(host.ssh_user, host.internal_ip, '{}22'.format(server.sequence_no))
            server.host = host
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


def veil_env_path(veil_env_name):
    return VEIL_HOME if veil_env_name in {'development', 'test'} else OPT_DIR / veil_env_name


def veil_home(veil_env_name):
    return VEIL_HOME if veil_env_name in {'development', 'test'} else OPT_DIR / veil_env_name / 'code' / 'app'


def veil_server(host_name, sequence_no, programs, deploys_via=None, resources=(), supervisor_http_port=None, name_servers=None, backup_mirror=None,
        memory_limit=None, cpu_share=None):
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
        'memory_limit': memory_limit,
        'cpu_share': cpu_share,
        'deploys_via': deploys_via
    })


def veil_host(internal_ip, external_ip, ssh_port=22, ssh_user='dejavu', lan_range='10.0.3', lan_interface='lxcbr0', mac_prefix='00:16:3e:73:bb',
        resources=()):
    from veil.model.collection import objectify
    return objectify({
        'internal_ip': internal_ip,
        'external_ip': external_ip,
        'ssh_port': ssh_port,
        'ssh_user': ssh_user,
        'lan_range': lan_range,
        'lan_interface': lan_interface,
        'mac_prefix': mac_prefix,
        'resources': resources,
        'deploys_via': '{}@{}:{}'.format(ssh_user, internal_ip, ssh_port)
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
