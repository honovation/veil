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
from .environment import split_veil_server_code


def veil_server(internal_ip, programs, deployed_via):
    from veil.model.collection import objectify

    return objectify({
        'internal_ip': internal_ip,
        'programs': programs,
        'deployed_via': deployed_via
    })


def get_veil_servers(env):
    return get_application().ENVIRONMENTS[env]


def get_current_veil_server():
    return get_application().ENVIRONMENTS[VEIL_ENV][VEIL_SERVER_NAME]


def is_current_veil_server_hosting(program_name):
    if VEIL_SERVER in ['test', 'development']:
        return True
    else:
        return program_name in get_current_veil_server().programs


def get_veil_server_internal_ip_hosting(program):
    if VEIL_SERVER in ['test', 'development']:
        return '127.0.0.1'
    for server in get_application().ENVIRONMENTS[VEIL_ENV].values():
        if program in server.programs:
            return server.internal_ip
    raise Exception('no server hosting program: {}'.format(program))


def get_remote_veil_server(code):
    env, server_name = split_veil_server_code(code)
    return get_application().ENVIRONMENTS[env][server_name]


def get_application_codebase():
    return get_application().CODEBASE


def get_application_name():
    codebase = get_application_codebase()
    return codebase[codebase.find('/') + 1:].replace('.git', '')


def get_application_architecture():
    return getattr(get_application(), 'ARCHITECTURE', {})


def get_application_components():
    return get_application_architecture().keys()


def get_application_settings():
    return getattr(get_application(), 'SETTINGS', {})


def get_application():
    import __veil__

    return __veil__

