from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *


PYRES_BASE_SETTINGS = {
    'queue': {
        'dbdir': VEIL_VAR_DIR / 'queue',
        'configfile': VEIL_ETC_DIR / 'queue.conf',
        'port': 6380
    },
    'resweb': {
        'config_file': VEIL_ETC_DIR / 'resweb.cfg',
        'queue_host': 'localhost',
        'queue_port': 6380,
        'server_host': 'localhost',
        'server_port': 5000
    },
    'supervisor': {
        'programs': {
            'queue': {
                'command': 'veil backend redis server up queue'
            },
            'resweb': {
                'command': 'resweb',
                'environment_variables': {
                    'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
                }
            }
        }
    }
}
