from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment.setting import *

@composite_installer('database_client')
def install_database_client():
    resources = []
    for component_name in set(get_settings().databases.values()):
        resources.append(component_resource(component_name))
    return [], resources