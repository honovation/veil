from __future__ import unicode_literals, print_function, division
from os import getenv
import platform
from veil.model.collection import DictObject
from veil_component import as_path

VEIL_APT_URL = 'http://mirrors.163.com/ubuntu/'
VEIL_DEPENDENCY_URL = 'http://dependency-veil.qiniudn.com'

PYPI_INDEX_URL = 'http://pypi.douban.com/simple/' # the official url "https://pypi.python.org/simple/" is blocked
PYPI_ARCHIVE_DIR = as_path('/opt/pypi')
PYPI_ARCHIVE_DIR.makedirs()

VEIL_TMP_DIR = as_path('/opt/tmp')
VEIL_TMP_DIR.makedirs()

VEIL_SERVER = getenv('VEIL_SERVER') or 'development'
VEIL_ENV = None
VEIL_SERVER_NAME = None
if '/' in VEIL_SERVER:
    VEIL_ENV, VEIL_SERVER_NAME = VEIL_SERVER.split('/', 1)
else:
    VEIL_ENV = VEIL_SERVER
    VEIL_SERVER_NAME = '@'
VEIL_ENV_TYPE = VEIL_ENV.rsplit('-', 1)[-1]  # development, test, staging, public (i.e. production)

_distname, _version, _codename = platform.linux_distribution()
VEIL_OS = DictObject(distname=_distname, version=_version, codename=_codename)
assert VEIL_OS.distname == 'Ubuntu' and VEIL_OS.codename in ('precise', 'trusty')
