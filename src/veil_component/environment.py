from __future__ import unicode_literals, print_function, division
from os import getenv
import os
from .path import as_path

VEIL_FRAMEWORK_CODEBASE = 'git@121.101.216.93:/opt/git/veil.git'

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = as_path(VEIL_HOME)

VEIL_FRAMEWORK_HOME = getenv('VEIL_FRAMEWORK_HOME')
VEIL_FRAMEWORK_HOME = as_path(VEIL_FRAMEWORK_HOME) if VEIL_FRAMEWORK_HOME else None