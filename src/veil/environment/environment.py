from __future__ import unicode_literals, print_function, division
import getpass
from os import getenv
import os
from veil.utility.path import *
from veil.server.os import *
from veil_component import *

def split_veil_server_code(code):
    env = code[:code.find('/')]
    server_name = code[code.find('/') + 1:]
    return env, server_name

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)
set_dynamic_dependencies_file(VEIL_HOME / 'dynamic-dependencies.txt')

VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')

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

BASIC_LAYOUT_RESOURCES = [
    directory_resource(path=VEIL_HOME / 'log'),
    directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
    directory_resource(path=VEIL_HOME / 'etc'),
    directory_resource(path=VEIL_ETC_DIR),
    directory_resource(path=VEIL_HOME / 'var'),
    directory_resource(path=VEIL_VAR_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
]
