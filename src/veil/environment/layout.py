from __future__ import unicode_literals, print_function, division
from os import getenv
import os
from sandal.event import *
from sandal.option import *
from sandal.path import *
from sandal.const import *
from sandal.collection import *
from .directory import create_directory

consts.EVENT_ENVIRONMENT_INSTALLING = 'environment-installing'

VEIL_HOME = getenv('VEIL_HOME') or '.'
VEIL_HOME = os.path.abspath(VEIL_HOME)
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = path(VEIL_HOME)

VEIL_ENV = getenv('VEIL_ENV') or 'development'
VEIL_LOG_DIR = VEIL_HOME / 'log' / VEIL_ENV
VEIL_ETC_DIR = VEIL_HOME / 'etc' / VEIL_ENV
VEIL_VAR_DIR = VEIL_HOME / 'var' / VEIL_ENV
VEIL_LAYOUT = objectify({
    'nginx': {
        'log_directory': VEIL_LOG_DIR / 'nginx',
        'config_file': VEIL_ETC_DIR / 'nginx.conf',
        'uploaded_files_directory': VEIL_VAR_DIR / 'uploaded-files',
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static'
    },
    'supervisor': {
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
})

def init_env():
    publish_event(consts.EVENT_ENVIRONMENT_INSTALLING, options=VEIL_LAYOUT)
    create_directory(VEIL_HOME / 'log')
    create_directory(VEIL_LOG_DIR)
    create_directory(VEIL_HOME / 'etc')
    create_directory(VEIL_ETC_DIR)
    create_directory(VEIL_HOME / 'var')
    create_directory(VEIL_VAR_DIR)
    return peek_options()