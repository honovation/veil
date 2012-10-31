from __future__ import unicode_literals, print_function, division
import getpass
from os import getenv
import os
import sys
from veil.utility.path import *
from veil.model.collection import *

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)
VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')

def split_veil_server_code(code):
    env = code[:code.find('/')]
    server_name = code[code.find('/') + 1:]
    return env, server_name

VEIL_SERVER = getenv('VEIL_SERVER') or 'development'
VEIL_ENV = None
VEIL_SERVER_NAME = None
if '/' in VEIL_SERVER:
    VEIL_ENV, VEIL_SERVER_NAME = split_veil_server_code(VEIL_SERVER)
else:
    VEIL_ENV = VEIL_SERVER
    VEIL_SERVER_NAME = '@'
VEIL_LOG_DIR = VEIL_HOME / 'log' / VEIL_ENV
VEIL_ETC_DIR = VEIL_HOME / 'etc' / VEIL_ENV
VEIL_VAR_DIR = VEIL_HOME / 'var' / VEIL_ENV

CURRENT_USER = os.getenv('SUDO_USER') or getpass.getuser()
CURRENT_USER_GROUP = CURRENT_USER
CURRENT_USER_HOME = as_path(os.getenv('HOME'))

def veil_server(internal_ip, programs, deployed_via):
    from veil.model.collection import objectify

    return objectify({
        'internal_ip': internal_ip,
        'programs': programs,
        'deployed_via': deployed_via
    })


def get_veil_servers(env):
    return sys.modules['__veil__'].ENVIRONMENTS[env]


def get_current_veil_server():
    return sys.modules['__veil__'].ENVIRONMENTS[VEIL_ENV][VEIL_SERVER_NAME]


def get_veil_server_hosting(program):
    if VEIL_SERVER in ['test', 'development']:
        return DictObject(internal_ip='127.0.0.1')
    for server in sys.modules['__veil__'].ENVIRONMENTS[VEIL_ENV].values():
        if program in server.programs:
            return server
    raise Exception('no server hosting program: {}'.format(program))


def get_remote_veil_server(code):
    env, server_name = split_veil_server_code(code)
    return sys.modules['__veil__'].ENVIRONMENTS[env][server_name]


def get_application_name():
    codebase = get_application_codebase()
    return codebase[codebase.find('/') + 1:].replace('.git', '')


def get_application_codebase():
    return get_application().CODEBASE


def get_application_components():
    return get_application_architecture().keys()


def get_application_architecture():
    return getattr(get_application(), 'ARCHITECTURE', {})


def get_application_tables():
    return getattr(get_application(), 'TABLES', {})


def get_application_settings():
    return getattr(get_application(), 'SETTINGS', {})


def get_application():
    if '__veil__' in sys.modules:
        __veil__ = sys.modules['__veil__']
    else:
        import __veil__
    return __veil__

