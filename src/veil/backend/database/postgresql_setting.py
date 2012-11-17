from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from veil.backend.database.database_client_setting import database_client_settings

def postgresql_settings(primary_purpose, *other_purposes, **updates):
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
        'databases': {
            primary_purpose: 'veil.backend.database.postgresql'
        }
    })
    total_settings = merge_settings(total_settings, database_client_settings(
        type='postgresql', purpose=primary_purpose, host=settings.host, port=settings.port,
        database=settings.database, schema=None, user=settings.user, password=settings.password
    ))
    for other_purpose in other_purposes:
        total_settings = merge_multiple_settings(total_settings, {
            '{}_postgresql'.format(other_purpose): DictObject(settings, database=other_purpose),
            'migration_commands': {
                '{}_postgresql'.format(other_purpose):
                    'veil backend database postgresql migrate {}'.format(other_purpose)
            },
            'databases': {
                other_purpose: 'veil.backend.database.postgresql'
            }
        }, database_client_settings(
            type='postgresql', purpose=other_purpose, host=settings.host, port=settings.port,
            database=other_purpose, schema=None, user=settings.user, password=settings.password
        ))
    return total_settings


def postgresql_server_program(purpose, updates=None):
    program = {
        'execute_command': 'veil backend database postgresql server-up {}'.format(purpose),
        'installer_providers': ['veil.backend.database.postgresql'],
        'resources': [('postgresql', dict(name=purpose))]
    }
    if updates:
        program.update(updates)
    return program