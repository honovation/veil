from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('database_client')
def install_database_client(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
        content=render_config(
        'database-client.cfg.j2', config=config)))
    resources.append(component_resource(config.driver))
    return [], resources


def load_database_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
        'driver', 'type', 'host', 'port', 'database', 'user', 'password', 'schema')
    config.port = int(config.port)
    return config