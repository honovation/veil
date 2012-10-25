from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from .server.pg_server_program import postgresql_server_program

def postgresql_settings(purpose, *other_purposes, **updates):
    settings = objectify({
        'host': get_veil_server_internal_ip_for('{}_postgresql'.format(purpose)),
        'port': 5432,
        'owner': CURRENT_USER,
        'data_directory': VEIL_VAR_DIR / '{}_postgresql'.format(purpose),
        'config_directory': VEIL_ETC_DIR / '{}_postgresql'.format(purpose),
        'unix_socket_directory': '/tmp',
        'database': purpose,
        'other_purposes': other_purposes
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
            primary_purpose = key.replace('_postgresql', '')
            other_purposes = set(value.other_purposes)
            for purpose in {primary_purpose}.union(other_purposes):
                new_settings = merge_settings(new_settings, {
                    'veil': {
                        '{}_database'.format(purpose): {
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