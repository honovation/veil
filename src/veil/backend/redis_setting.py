from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *

REDIS_BASE_SETTINGS = {
    'redis': {
        'owner': CURRENT_USER,
        'owner_group': CURRENT_USER_GROUP,
        'bind': 'localhost',
        'port': 6379,
        'dbdir': VEIL_VAR_DIR / 'redis',
        'configfile': VEIL_ETC_DIR / 'redis.conf'
    }
}

def redis_settings(primary_purpose, *other_purposes, **updates):
    settings = objectify({
        'owner': CURRENT_USER,
        'owner_group': CURRENT_USER_GROUP,
        'bind': get_veil_server_internal_ip_hosting('{}_redis'.format(primary_purpose)),
        'port': 6379,
        'password': '',
        'dbdir': VEIL_VAR_DIR / '{}_redis'.format(primary_purpose),
        'configfile': VEIL_ETC_DIR / '{}_redis.conf'.format(primary_purpose)
    })
    settings = merge_settings(settings, updates, overrides=True)
    if 'test' == VEIL_ENV:
        settings = merge_settings(settings, {
            'port': int(settings.port) + 1
        }, overrides=True)
    total_settings =  objectify({
        '{}_redis'.format(primary_purpose): settings,
        'supervisor': {
            'programs': {
                '{}_redis'.format(primary_purpose): redis_server_program(primary_purpose)
            }
        }
    })
    for other_purpose in other_purposes:
        total_settings['{}_redis'.format(other_purpose)] = settings
    return total_settings

def redis_server_program(purpose):
    return {
        'execute_command': 'veil backend redis server-up {}'.format(purpose),
        'installer_providers': ['veil.backend.redis'],
        'resources': [('redis', dict(name=purpose))]
    }