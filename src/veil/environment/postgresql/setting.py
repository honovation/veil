from __future__ import unicode_literals, print_function, division
from veil.layout import *


POSTGRESQL_BASE_SETTINGS = {
    'postgresql': {
        'data_directory': VEIL_VAR_DIR / 'postgresql',
        'config_directory': VEIL_ETC_DIR,
        'unix_socket_directory': '/tmp'
    },
    'supervisor': {
        'programs': {
            'postgresql': {
                'command': 'veil environment postgresql server up'
            }
        }
    }
}