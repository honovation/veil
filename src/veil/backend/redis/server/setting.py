from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *

REDIS_BASE_SETTINGS = {
    'redis': {
        'dbdir': VEIL_VAR_DIR / 'redis',
        'configfile': VEIL_ETC_DIR / 'redis.conf'
    },
    'supervisor': {
        'programs': {
            'redis': {
                'command': 'veil backend redis server up'
            }
        }
    }
}