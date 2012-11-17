from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.model.collection import *

def database_client_settings(type, driver, purpose, host, port, database, schema, user, password):
    return {
        '{}_database_client'.format(purpose): {
            'type': type,
            'driver': driver,
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'schema': schema
        }
    }


def list_database_client_options():
    database_client_options = {}
    for key, value in get_settings().items():
        if key.endswith('_database_client'):
            purpose = key.replace('_database_client', '')
            database_client_options[purpose] = get_database_client_options(purpose)
    return database_client_options


def get_database_client_options(purpose):
    config = get_settings()['{}_database_client'.format(purpose)]
    return objectify({
        'type': config.type,
        'driver': config.driver,
        'host': config.host,
        'port': config.port,
        'database': config.database,
        'user': config.user,
        'password': config.password,
        'schema': config.schema
    })
