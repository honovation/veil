from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.model.collection import *

def database_client_settings(type, purpose, host, port, database, schema, user, password):
    return {
        '{}_database_client'.format(purpose): {
            'type': type,
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'schema': schema
        }
    }


def get_database_client_options(purpose):
    config = get_settings()['{}_database_client'.format(purpose)]
    return objectify({
        'type': config.type,
        'host': config.host,
        'port': config.port,
        'database': config.database,
        'user': config.user,
        'password': config.password,
        'schema': config.schema
    })
