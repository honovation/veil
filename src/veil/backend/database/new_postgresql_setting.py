from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def postgresql_program(purpose, host, port, owner, owner_password, user, password):
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': 'postgres -D {}'.format(VEIL_VAR_DIR / '{}_postgresql'.format(purpose)),
            'installer_providers': ['veil.backend.database.postgresql'],
            'postgresql_resource': {
                'purpose': purpose,
                'host': host,
                'port': port,
                'owner': owner,
                'owner_password': owner_password,
                'user': user,
                'password': password
            }
        }
    })