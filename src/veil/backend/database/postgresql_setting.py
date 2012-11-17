from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from veil.model.event import *

EVENT_NEW_POSTGRESQL = 'new-postgresql'

def init():
    register_settings_coordinator(copy_postgresql_settings_into_veil)


def postgresql_settings(primary_purpose, *other_purposes, **updates):
    publish_event(EVENT_NEW_POSTGRESQL, purpose=primary_purpose)
    settings = objectify({
        'host': get_veil_server_internal_ip_hosting('{}_postgresql'.format(primary_purpose)),
        'port': 5432,
        'owner': CURRENT_USER,
        'data_directory': VEIL_VAR_DIR / '{}_postgresql'.format(primary_purpose),
        'config_directory': VEIL_ETC_DIR / '{}_postgresql'.format(primary_purpose),
        'unix_socket_directory': '/tmp',
        'database': primary_purpose
    })
    settings = merge_settings(settings, updates, overrides=True)
    if 'test' == VEIL_ENV:
        settings = merge_settings(settings, {
            'port': int(settings.port) + 1
        }, overrides=True)
    total_settings = objectify({
        '{}_postgresql'.format(primary_purpose): settings,
        'supervisor': {
            'programs': {
                '{}_postgresql'.format(primary_purpose): postgresql_server_program(primary_purpose)
            }
        },
        'self_checkers': {
            'migration-scripts': 'veil.backend.database.postgresql.check_if_locked_migration_scripts_being_changed'
        },
        'migration_commands': {
            '{}_postgresql'.format(primary_purpose):
                'veil backend database postgresql migrate {}'.format(primary_purpose)
        },
        'reset_commands': {
            '{}_postgresql'.format(primary_purpose):
                'veil backend database postgresql reset {}'.format(primary_purpose)
        },
        'databases': {
            primary_purpose: 'veil.backend.database.postgresql'
        }
    })
    for other_purpose in other_purposes:
        total_settings = merge_settings(total_settings, {
            '{}_postgresql'.format(other_purpose): DictObject(settings, database=other_purpose),
            'migration_commands': {
                '{}_postgresql'.format(other_purpose):
                    'veil backend database postgresql migrate {}'.format(other_purpose)
            },
            'reset_commands': {
                '{}_postgresql'.format(other_purpose):
                    'veil backend database postgresql reset {}'.format(other_purpose)
            },
            'databases': {
                other_purpose: 'veil.backend.database.postgresql'
            }
        })
    return total_settings


def copy_postgresql_settings_into_veil(settings):
    new_settings = settings
    for key, value in settings.items():
        if key.endswith('_postgresql'):
            primary_purpose = key.replace('_postgresql', '')
            new_settings = merge_settings(new_settings, {
                'veil': {
                    '{}_database'.format(primary_purpose): {
                        'type': 'postgresql',
                        'host': value.host,
                        'port': value.port,
                        'user': value.user,
                        'password': value.password,
                        'database': value.database
                    }
                }
            }, overrides=True)
    return objectify(new_settings)


def postgresql_server_program(purpose, updates=None):
    program = {
        'execute_command': 'veil backend database postgresql server-up {}'.format(purpose),
        'installer_providers': ['veil.backend.database.postgresql'],
        'resources': [('postgresql', dict(name=purpose))]
    }
    if updates:
        program.update(updates)
    return program

init()