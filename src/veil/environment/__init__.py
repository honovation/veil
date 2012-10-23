from __future__ import unicode_literals, print_function, division
import getpass
from os import getenv
import os
from veil.utility.path import *

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)
VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')

VEIL_SERVER = getenv('VEIL_SERVER') or 'development'
VEIL_ENV = None
VEIL_SERVER_NAME = None
if '/' in VEIL_SERVER:
    VEIL_ENV = VEIL_SERVER[:VEIL_SERVER.find('/')]
    VEIL_SERVER_NAME = VEIL_SERVER[VEIL_SERVER.find('/') + 1:]
else:
    VEIL_ENV = VEIL_SERVER
    VEIL_SERVER_NAME = '@'
VEIL_LOG_DIR = VEIL_HOME / 'log' / VEIL_ENV
VEIL_ETC_DIR = VEIL_HOME / 'etc' / VEIL_ENV
VEIL_VAR_DIR = VEIL_HOME / 'var' / VEIL_ENV

CURRENT_USER = os.getenv('SUDO_USER') or getpass.getuser()
CURRENT_USER_GROUP = CURRENT_USER

def veil_server(internal_ip, programs, external_ip, external_ssh_port):
    from veil.model.collection import objectify

    return objectify({
        'internal_ip': internal_ip,
        'programs': programs,
        'external_ip': external_ip,
        'external_ssh_port': external_ssh_port
    })


def get_current_veil_server():
    import __veil__

    return __veil__.ENVIRONMENTS[VEIL_ENV][VEIL_SERVER_NAME]


def get_veil_server_internal_ip_for(program):
    import __veil__

    if VEIL_SERVER in ['test', 'development']:
        return '127.0.0.1'
    for server in __veil__.ENVIRONMENTS[VEIL_ENV].values():
        if program in server.programs:
            return program.internal_ip
    raise Exception('no server hosting program: {}'.format(program))
