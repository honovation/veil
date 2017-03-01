from __future__ import unicode_literals, print_function, division
import os
import platform
from os import getenv
from collections import namedtuple
from .path import as_path


class VeilEnv(object):
    def __init__(self, name):
        super(VeilEnv, self).__init__()
        self.name = name
        self.base_name = self.name.rsplit('--', 1)[0]
        self.type = self.base_name.rsplit('-', 1)[-1]

    @property
    def is_dev(self):
        return self.type in ('dev', 'development')

    @property
    def is_test(self):
        return self.type == 'test'

    @property
    def is_staging(self):
        return self.type == 'staging'

    @property
    def is_prod(self):
        return self.type in ('prod', 'production', 'public')

    def __eq__(self, other):
        if not isinstance(other, VeilEnv):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return 'VEIL ENVIRONMENT <{}>'.format(self.name)


VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')
VEIL_FRAMEWORK_HOME = as_path(VEIL_FRAMEWORK_HOME) if VEIL_FRAMEWORK_HOME else None

VEIL_HOME = os.path.abspath(getenv('VEIL_HOME') or '.')
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)

VEIL_SERVER_NAME = getenv('VEIL_SERVER_NAME') or 'development'
if '/' in VEIL_SERVER_NAME:
    VEIL_ENV_NAME, VEIL_SERVER_NAME = VEIL_SERVER_NAME.rsplit('/', 1)
elif VEIL_SERVER_NAME == 'test':
    VEIL_ENV_NAME, VEIL_SERVER_NAME = VEIL_SERVER_NAME, 'test-server'
else:
    VEIL_ENV_NAME, VEIL_SERVER_NAME = VEIL_SERVER_NAME, 'dev-server'
VEIL_ENV = VeilEnv(VEIL_ENV_NAME)

CURRENT_OS = namedtuple('VeilOS', 'distname, version, codename')(*platform.linux_distribution())
assert CURRENT_OS.distname == 'Ubuntu' and CURRENT_OS.codename in ('trusty', 'xenial')
