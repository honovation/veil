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