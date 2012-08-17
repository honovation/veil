from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *


def postgresql_program(purpose='default', updates=None):
    program = {'command': 'veil backend database postgresql server up {}'.format(purpose)}
    if updates:
        program.update(updates)
    return program


def postgresql_settings(purpose='default', **updates):
    settings = {
        'listen_addresses': 'localhost',
        'host': 'localhost',
        'port': 5432,
        'owner': CURRENT_USER,
        'data_directory': VEIL_VAR_DIR / '{}_postgresql'.format(purpose),
        'config_directory': VEIL_ETC_DIR / '{}_postgresql'.format(purpose),
        'unix_socket_directory': '/tmp',
        'database': purpose
    }
    settings.update(updates)
    return objectify({'{}_postgresql'.format(purpose): settings})


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