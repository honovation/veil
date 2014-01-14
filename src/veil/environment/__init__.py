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


def veil_server(hosted_on, sequence_no, programs, deploys_via=None, resources=(), supervisor_http_port=None,
                dns='8.8.8.8', backup_mirror=None, backup_dirs=[], memory_limit=None):
    from veil.model.collection import objectify

    return objectify({
        'hosted_on': hosted_on,
        'sequence_no': sequence_no,
        'programs': programs,
        'deploys_via': deploys_via,
        'resources': resources,
        'supervisor_http_port': supervisor_http_port,
        'dns': dns,
        'backup_mirror': backup_mirror,
        'backup_dirs': backup_dirs,
        'memory_limit': memory_limit
    })


def veil_host(internal_ip, external_ip, ssh_port=22, ssh_user='dejavu',
              lan_range='10.0.3', lan_interface='lxcbr0', mac_prefix='00:16:3e:73:bb',
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


def list_veil_server_names(veil_env):
    env = get_application().ENVIRONMENTS[veil_env]
    return env.sorted_server_names or sorted(env.servers.keys())


def list_veil_servers(veil_env):
    return get_application().ENVIRONMENTS[veil_env].servers


def list_veil_hosts(veil_env):
    return get_application().ENVIRONMENTS[veil_env].server_hosts


def get_veil_env_deployment_memo(veil_env):
    return get_application().ENVIRONMENTS[veil_env].deployment_memo


def get_veil_host(veil_env, veil_host_name):
    return list_veil_hosts(veil_env)[veil_host_name]


def get_veil_server(veil_env, veil_server_name):
    return list_veil_servers(veil_env)[veil_server_name]


def get_current_veil_server():
    return get_veil_server(VEIL_ENV, VEIL_SERVER_NAME)


def get_veil_server_deploys_via(veil_env, veil_server_name):
    veil_server = get_veil_server(veil_env, veil_server_name)
    veil_host_name = veil_server.hosted_on
    veil_host = get_veil_host(veil_env, veil_host_name)
    return veil_server.deploys_via or '{}@{}:{}'.format(
        veil_host.ssh_user,
        veil_host.internal_ip,
        '{}22'.format(veil_server.sequence_no))


def get_application_codebase():
    return get_application().CODEBASE


def get_application():
    import __veil__

    return __veil__

