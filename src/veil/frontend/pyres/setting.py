from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *


PYRES_BASE_SETTINGS = {
    'queue': {
        'dbdir': VEIL_VAR_DIR / 'queue',
        'configfile': VEIL_ETC_DIR / 'queue.conf',
        'port': 6380
    },
    'supervisor': {
        'programs': {
            'queue': {
                'command': 'veil backend redis server up queue'
            }
        }
    }
}