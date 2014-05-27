from __future__ import unicode_literals, print_function, division
from os import getenv
import platform
from veil.model.collection import DictObject

VEIL_APT_URL = 'http://mirrors.163.com/ubuntu/'
VEIL_DEPENDENCY_URL = 'http://dependency-veil.qiniudn.com'
PYPI_INDEX_URL = '-i http://pypi.douban.com/simple/' # the official url "https://pypi.python.org/simple/" is blocked

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
VEIL_ENV_TYPE = VEIL_ENV.rsplit('-', 1)[-1]  # development, test, staging, public (i.e. production)

_distname, _version, _codename = platform.linux_distribution()
VEIL_OS = DictObject(distname=_distname, version=_version, codename=_codename)
assert VEIL_OS.distname == 'Ubuntu' and VEIL_OS.codename in ('precise', 'trusty')
