from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *

REDIS_BASE_SETTINGS = {
    'redis': {
        'owner': CURRENT_USER,
        'owner_group': CURRENT_USER_GROUP,
        'host': 'localhost',
        'port': 6379,
        'dbdir': VEIL_VAR_DIR / 'redis',
        'configfile': VEIL_ETC_DIR / 'redis.conf'
    }
}

def redis_program(purpose='redis'):
    return {
        'command': 'veil backend redis server up {}'.format(purpose)
    }
