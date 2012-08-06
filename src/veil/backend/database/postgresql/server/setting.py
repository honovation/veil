from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *


POSTGRESQL_BASE_SETTINGS = {
    'postgresql': {
        'listen_addresses': 'localhost',
        'host': 'localhost',
        'port': 5432,
        'owner': CURRENT_USER,
        'data_directory': VEIL_VAR_DIR / 'postgresql',
        'config_directory': VEIL_ETC_DIR,
        'unix_socket_directory': '/tmp'
    }
}

def postgresql_program(updates=None):
    program = {'command': 'veil backend database postgresql server up'}
    if updates:
        program.update(updates)
    return program
