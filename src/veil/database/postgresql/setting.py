from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *


POSTGRESQL_BASE_SETTINGS = {
    'postgresql': {
        'data_directory': VEIL_VAR_DIR / 'postgresql',
        'config_directory': VEIL_ETC_DIR,
        'unix_socket_directory': '/tmp'
    },
    'supervisor': {
        'programs': {
            'postgresql': {
                'command': 'veil database postgresql server up'
            }
        }
    }
}