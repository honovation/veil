from __future__ import unicode_literals, print_function, division
import getpass
from os import getenv
import os
from veil.utility.path import *

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)

VEIL_SERVER = getenv('VEIL_SERVER') or 'development'
VEIL_ENV = None
VEIL_ENV_SERVER = None
if '/' in VEIL_SERVER:
    VEIL_ENV = VEIL_SERVER[:VEIL_SERVER.find('/')]
    VEIL_ENV_SERVER = VEIL_SERVER[VEIL_SERVER.find('/') + 1:]
else:
    VEIL_ENV = VEIL_SERVER
VEIL_LOG_DIR = VEIL_HOME / 'log' / VEIL_ENV
VEIL_ETC_DIR = VEIL_HOME / 'etc' / VEIL_ENV
VEIL_VAR_DIR = VEIL_HOME / 'var' / VEIL_ENV

CURRENT_USER = os.getenv('SUDO_USER') or getpass.getuser()
CURRENT_USER_GROUP = CURRENT_USER