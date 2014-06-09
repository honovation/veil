from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME
from .environment import VEIL_FRAMEWORK_HOME
from .environment import VEIL_FRAMEWORK_CODEBASE
from .environment import VEIL_LOG_DIR
from .environment import VEIL_ETC_DIR
from .environment import VEIL_VAR_DIR
from .environment import VEIL_SERVER
from .environment import VEIL_ENV
from .environment import VEIL_ENV_TYPE
from .environment import VEIL_DEPENDENCY_URL
from .environment import VEIL_APT_URL
from .environment import PYPI_INDEX_URL
from .environment import PYPI_ARCHIVE_DIR
from .environment import VEIL_TMP_DIR
from .environment import CURRENT_OS
from .environment import VEIL_SERVER_NAME
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
            VEIL_ENV, sorted_server_names, server_names)
    else:
        sorted_server_names = sorted(server_names)

    from veil.model.collection import objectify
    env = objectify({'hosts': hosts, 'servers': servers, 'sorted_server_names': sorted_server_names, 'deployment_memo': deployment_memo})
    for server_name, server in env.servers.items():
        server.env_name = name
        server.name = server_name
        server.container_name = '{}-{}'.format(server.env_name, server.name)
        server.start_order = 1000 + 10 * sorted_server_names.index(server_name) if sorted_server_names else 0
        server.host = None
    for host_name, host in env.hosts.items():
        host.env_name = name
        host.name = host_name
        # host base_name can be used to determine host config dir: as_path('{}/{}/hosts/{}'.format(config_dir, host.env_name, host.base_name))
        host.base_name = host_name.split('/', 1)[0]  # e.g. ljhost-005/3 => ljhost-005
        host.server_list = []
        for server_name, server in env.servers.items():
            if host.name != server.host_name:
                continue
            server.host = host
            host.server_list.append(server)
        host.server_list.sort(key=lambda s: env.sorted_server_names.index(s.name))

    if env.hosts:
        assert all(host.server_list for host in env.hosts.values()), 'ENV {}: found host without server(s)'.format(VEIL_ENV)
        assert all(server.host for server in env.servers.values()), 'ENV {}: found server without host'.format(VEIL_ENV)
        assert all(len(host.server_list) == len(set(server.sequence_no for server in host.server_list)) for host in env.hosts.values()), \
            'ENV {}: found sequence no conflict among servers on one host'.format(VEIL_ENV)

    # break cyclic reference between host and server to get freeze_dict_object out of complain
    for server in env.servers.values():
        del server.host

    return env


def veil_server(host_name, sequence_no, programs, deploys_via=None, resources=(), supervisor_http_port=None, name_servers=None, backup_mirror=None,
        backup_dirs=None, memory_limit=None, cpu_share=None):
    from veil.model.collection import objectify
    return objectify({
        'host_name': host_name,
        'sequence_no': sequence_no,
        'programs': programs,
        'deploys_via': deploys_via,
        'resources': resources,
        'supervisor_http_port': supervisor_http_port,
        'name_servers': name_servers or ['114.114.114.114', '114.114.115.115', '8.8.8.8', '8.8.4.4'],
        'backup_mirror': backup_mirror,
        'backup_dirs': backup_dirs or [],
        'memory_limit': memory_limit,
        'cpu_share': cpu_share
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
        'resources': resources
    })


def list_veil_server_names(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].sorted_server_names


def list_veil_servers(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].servers


def get_veil_server(veil_env_name, veil_server_name):
    return list_veil_servers(veil_env_name)[veil_server_name]


def get_current_veil_server():
    return get_veil_server(VEIL_ENV, VEIL_SERVER_NAME)


def list_veil_hosts(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].hosts


def get_veil_host(veil_env_name, veil_host_name):
    return list_veil_hosts(veil_env_name)[veil_host_name]


def get_veil_env_deployment_memo(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].deployment_memo


def get_veil_server_deploys_via(veil_env_name, veil_server_name):
    server = get_veil_server(veil_env_name, veil_server_name)
    if server.deploys_via:
        return server.deploys_via
    host = get_veil_host(veil_env_name, server.host_name)
    return '{}@{}:{}'.format(host.ssh_user, host.internal_ip, '{}22'.format(server.sequence_no))


def get_application_codebase():
    return get_application().CODEBASE


def get_application():
    import __veil__

    return __veil__
