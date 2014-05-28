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
from .environment import VEIL_OS
from .environment import VEIL_SERVER_NAME
from .environment import CURRENT_USER
from .environment import CURRENT_USER_GROUP
from .environment import CURRENT_USER_HOME
from .environment import BASIC_LAYOUT_RESOURCES
from .environment import get_application_version
from .environment import get_veil_framework_version

def veil_env(server_hosts, servers, sorted_server_names=None, deployment_memo=None):
    from veil.model.collection import objectify

    return objectify({
        'server_hosts': server_hosts,
        'servers': servers,
        'sorted_server_names': sorted_server_names,
        'deployment_memo': deployment_memo
    })


def veil_server(hosted_on, sequence_no, programs, deploys_via=None, resources=(), supervisor_http_port=None, name_servers=None, backup_mirror=None,
        backup_dirs=None, memory_limit=None, cpu_share=None):
    from veil.model.collection import objectify
    name_servers = name_servers or ['114.114.114.114', '114.114.115.115', '8.8.8.8', '8.8.4.4']
    return objectify({
        'hosted_on': hosted_on,
        'sequence_no': sequence_no,
        'programs': programs,
        'deploys_via': deploys_via,
        'resources': resources,
        'supervisor_http_port': supervisor_http_port,
        'name_servers': name_servers,
        'backup_mirror': backup_mirror,
        'backup_dirs': backup_dirs or [],
        'memory_limit': memory_limit,
        'cpu_share': cpu_share
    })


def veil_host(internal_ip, external_ip, ssh_port=22, ssh_user='dejavu', lan_range='10.0.3', lan_interface='lxcbr0', mac_prefix='00:16:3e:73:bb',
        override_sources_list=False, enable_unattended_upgrade=False, resources=()):
    from veil.model.collection import objectify

    return objectify({
        'internal_ip': internal_ip,
        'external_ip': external_ip,
        'ssh_port': ssh_port,
        'ssh_user': ssh_user,
        'lan_range': lan_range,
        'lan_interface': lan_interface,
        'mac_prefix': mac_prefix,
        'override_sources_list': override_sources_list,
        'enable_unattended_upgrade': enable_unattended_upgrade,
        'resources': resources
    })


def list_veil_server_names(veil_env_name):
    env = get_application().ENVIRONMENTS[veil_env_name]
    return env.sorted_server_names or sorted(env.servers.keys())


def list_veil_servers(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].servers


def list_veil_hosts(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].server_hosts


def get_veil_env_deployment_memo(veil_env_name):
    return get_application().ENVIRONMENTS[veil_env_name].deployment_memo


def get_veil_host(veil_env_name, veil_host_name):
    return list_veil_hosts(veil_env_name)[veil_host_name]


def get_veil_server(veil_env_name, veil_server_name):
    return list_veil_servers(veil_env_name)[veil_server_name]


def get_current_veil_server():
    return get_veil_server(VEIL_ENV, VEIL_SERVER_NAME)


def get_veil_server_deploys_via(veil_env_name, veil_server_name):
    veil_server = get_veil_server(veil_env_name, veil_server_name)
    veil_host_name = veil_server.hosted_on
    veil_host = get_veil_host(veil_env_name, veil_host_name)
    return veil_server.deploys_via or '{}@{}:{}'.format(
        veil_host.ssh_user,
        veil_host.internal_ip,
        '{}22'.format(veil_server.sequence_no))


def get_application_codebase():
    return get_application().CODEBASE


def get_application():
    import __veil__

    return __veil__
