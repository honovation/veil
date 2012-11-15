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

def init():
    register_settings_coordinator(copy_redis_settings_to_veil)


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
        settings.port = int(settings.port) + 1
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


def copy_redis_settings_to_veil(settings):
    new_settings = settings
    for key, value in settings.items():
        if key.endswith('_redis'):
            new_settings = merge_settings(new_settings, {
                'veil': {
                    key: {
                        'host': value.bind,
                        'port': value.port,
                        'password': value.password
                    }
                }
            }, overrides=True)
    return new_settings

init()