from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.backend.database.database_client_setting import list_database_client_options

@composite_installer('database_client')
def install_database_client():
    resources = []
    for purpose, database_client_options in list_database_client_options().items():
        resources.append(component_resource(database_client_options.driver))
    return [], resources