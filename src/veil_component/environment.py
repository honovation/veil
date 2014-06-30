from __future__ import unicode_literals, print_function, division
import os
import platform
from os import getenv
from collections import namedtuple
from .path import as_path


VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')
VEIL_FRAMEWORK_HOME = as_path(VEIL_FRAMEWORK_HOME) if VEIL_FRAMEWORK_HOME else None

VEIL_HOME = os.path.abspath(getenv('VEIL_HOME') or '.')
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)

VEIL_SERVER_NAME = getenv('VEIL_SERVER_NAME') or 'development'
if '/' in VEIL_SERVER_NAME:
    VEIL_ENV_NAME, VEIL_SERVER_NAME = VEIL_SERVER_NAME.rsplit('/', 1)
else:
    VEIL_ENV_NAME, VEIL_SERVER_NAME = VEIL_SERVER_NAME, '@'
VEIL_ENV_SHORT_NAME = VEIL_ENV_NAME.rsplit('--', 1)[0]
VEIL_ENV_TYPE = VEIL_ENV_SHORT_NAME.rsplit('-', 1)[-1]  # development, test, staging, public (i.e. production)

CURRENT_OS = namedtuple('VeilOS', 'distname, version, codename')(*platform.linux_distribution())
# TODO: update after every dev upgrades to trusty
assert CURRENT_OS.distname == 'Ubuntu' and (VEIL_ENV_TYPE in ('development', 'test') or CURRENT_OS.codename in ('trusty',))
