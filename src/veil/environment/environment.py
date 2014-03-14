from __future__ import unicode_literals, print_function, division
import getpass
import os
from veil_component import *
from veil.server.os import *
from veil.env_const import *

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

_application_version = None
def get_application_version():
    if 'development' == VEIL_SERVER:
        return 'development'
    if 'test' == VEIL_SERVER:
        return 'test'
    global _application_version
    from veil.utility.shell import shell_execute

    if not _application_version:
        app_commit_hash = shell_execute('git rev-parse HEAD', cwd=VEIL_HOME, capture=True).strip()
        framework_commit_hash = get_veil_framework_version()
        _application_version = '{}-{}'.format(app_commit_hash, framework_commit_hash)
    return _application_version


def get_veil_framework_version():
    from veil.utility.shell import shell_execute

    return shell_execute('git rev-parse HEAD', cwd=VEIL_FRAMEWORK_HOME, capture=True).strip()