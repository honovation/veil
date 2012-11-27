from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def postgresql_program(
        purpose, host, port, owner, owner_password, user, password,
        log_min_duration_statement):
    data_dir = VEIL_VAR_DIR / '{}-postgresql'.format(purpose.replace('_', '-'))
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': 'postgres -D {}'.format(data_dir),
            'migrate_command': 'veil backend database postgresql migrate {}'.format(purpose),
            'resources': [('veil.backend.database.postgresql.postgresql_server_resource', {
                'purpose': purpose,
                'config': {
                    'host': host,
                    'port': port,
                    'owner': owner,
                    'owner_password': owner_password,
                    'user': user,
                    'password': password,
                    'log_min_duration_statement': log_min_duration_statement
                }
            })]
        }
    })