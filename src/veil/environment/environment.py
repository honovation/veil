from __future__ import unicode_literals, print_function, division
import getpass
import os
from veil_component import *
from veil.server.os import *


APT_URL = 'http://mirrors.163.com/ubuntu/'
DEPENDENCY_URL = 'http://dependency-veil.qiniudn.com'
PYPI_INDEX_URL = 'http://pypi.douban.com/simple/' # the official url "https://pypi.python.org/simple/" is blocked

OPT_DIR = as_path('/opt')
HOST_SHARE_DIR = OPT_DIR / 'share'
DEPENDENCY_DIR = HOST_SHARE_DIR / 'dependency'
DEPENDENCY_INSTALL_DIR = HOST_SHARE_DIR / 'dependency-install'
PYPI_ARCHIVE_DIR = HOST_SHARE_DIR / 'pypi'

VEIL_LOG_DIR = VEIL_HOME / 'log' / VEIL_ENV_NAME
VEIL_ETC_DIR = VEIL_HOME / 'etc' / VEIL_ENV_NAME
VEIL_VAR_DIR = VEIL_HOME / 'var' / VEIL_ENV_NAME

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

VEIL_FRAMEWORK_CODEBASE = 'git@ljhost-003.dmright.com:/opt/git/veil.git'

_application_version = None
def get_application_version():
    if VEIL_ENV_TYPE in {'development', 'test'}:
        return  VEIL_ENV_TYPE
    global _application_version
    from veil.utility.shell import shell_execute
    if not _application_version:
        app_commit_hash = shell_execute('git rev-parse HEAD', cwd=VEIL_HOME, capture=True)
        framework_commit_hash = get_veil_framework_version()
        _application_version = '{}-{}'.format(app_commit_hash, framework_commit_hash)
    return _application_version


def get_veil_framework_version():
    from veil.utility.shell import shell_execute
    return shell_execute('git rev-parse HEAD', cwd=VEIL_FRAMEWORK_HOME, capture=True)