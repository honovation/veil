from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from .server.pg_server_program import postgresql_server_program

def postgresql_settings(purpose, **updates):
    settings = objectify({
        'host': '127.0.0.1',
        'port': 5432,
        'owner': CURRENT_USER,
        'data_directory': VEIL_VAR_DIR / '{}_postgresql'.format(purpose),
        'config_directory': VEIL_ETC_DIR / '{}_postgresql'.format(purpose),
        'unix_socket_directory': '/tmp',
        'database': purpose
    })
    settings = merge_settings(settings, updates, overrides=True)
    if 'test' == VEIL_ENV:
        settings.port += 1
    return objectify({
        '{}_postgresql'.format(purpose): settings,
        'supervisor': {
            'programs': {
                '{}_postgresql'.format(purpose): postgresql_server_program(purpose)
            }
        }
    })


def copy_postgresql_settings_into_veil(settings):
    new_settings = settings
    for key, value in settings.items():
        if key.endswith('_postgresql'):
            new_settings = merge_settings(new_settings, {
                'veil': {
                    key.replace('_postgresql', '_database'): {
                        'type': 'postgresql',
                        'host': value.host,
                        'port': value.port,
                        'user': value.user,
                        'password': value.password,
                        'database': value.database
                    }
                }
            }, overrides=True)
    return new_settings