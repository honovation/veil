from __future__ import unicode_literals, print_function, division

def database_client_resource(purpose, driver, type, host, port, database, user, password, schema):
    return ('veil.backend.database.client.database_client_resource', {
        'purpose': purpose,
        'config': {
            'driver': driver,
            'type': type,
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'schema': schema
        }})