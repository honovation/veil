from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME
from .environment import VEIL_FRAMEWORK_HOME
from .environment import VEIL_LOG_DIR
from .environment import VEIL_ETC_DIR
from .environment import VEIL_VAR_DIR
from .environment import VEIL_SERVER
from .environment import VEIL_ENV
from .environment import VEIL_SERVER_NAME
from .environment import CURRENT_USER
from .environment import CURRENT_USER_GROUP
from .environment import CURRENT_USER_HOME
from .environment import BASIC_LAYOUT_RESOURCES


def veil_env(server_hosts, servers, deployment_memo=None):
    from veil.model.collection import objectify

    return objectify({
        'server_hosts': server_hosts,
        'servers': servers,
        'deployment_memo': deployment_memo
    })


def veil_server(hosted_on, sequence_no, programs, resources=(), supervisor_http_port=None):
    from veil.model.collection import objectify

    return objectify({
        'hosted_on': hosted_on,
        'sequence_no': sequence_no,
        'programs': programs,
        'resources': resources,
        'supervisor_http_port': supervisor_http_port
    })


def veil_host(ssh_ip, ssh_port=22, ssh_user='dejavu',
              lan_range='10.0.3', lan_interface='lxcbr0', mac_prefix='00:16:3e:73:bb',
              resources=()):
    from veil.model.collection import objectify

    return objectify({
        'ssh_ip': ssh_ip,
        'ssh_port': ssh_port,
        'ssh_user': ssh_user,
        'lan_range': lan_range,
        'lan_interface': lan_interface,
        'mac_prefix': mac_prefix,
        'resources': resources
    })


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
    return '{}@{}:{}'.format(
        veil_host.ssh_user,
        veil_host.ssh_ip,
        '{}22'.format(veil_server.sequence_no))


def get_application_codebase():
    return get_application().CODEBASE


def get_application_architecture():
    return getattr(get_application(), 'ARCHITECTURE', {})


def get_application_components():
    return get_application_architecture().keys()


def get_application_version():
    if 'development' == VEIL_SERVER:
        return 'development'
    if 'test' == VEIL_SERVER:
        return 'test'
    from veil.utility.shell import shell_execute

    app_commit_hash = shell_execute('git rev-parse HEAD', cwd=VEIL_HOME, capture=True).strip()
    framework_commit_hash = get_veil_framework_version()
    return '{}-{}'.format(app_commit_hash, framework_commit_hash)


def get_veil_framework_version():
    from veil.utility.shell import shell_execute

    return shell_execute('git rev-parse HEAD', cwd=VEIL_FRAMEWORK_HOME, capture=True).strip()


def get_application():
    import __veil__

    return __veil__

