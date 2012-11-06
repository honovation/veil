from __future__ import unicode_literals, print_function, division

def db2_settings(purpose, host, port, database, schema, user, password):
    return {
        'veil': {
            '{}_database'.format(purpose): {
                'type': 'db2',
                'host': host,
                'port': port,
                'database': database,
                'user': user,
                'password': password,
                'schema': schema
            }
        }
    }