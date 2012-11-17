from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.backend.database.database_client_setting import database_client_settings

def db2_settings(purpose, host, port, database, schema, user, password):
    return database_client_settings(
        type='db2', driver='veil.backend.database.db2', purpose=purpose, host=host, port=port,
        database=database, schema=schema, user=user, password=password
    )