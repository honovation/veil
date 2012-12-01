from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

@composite_installer
def database_client_resource(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
        content=render_config(
        'database-client.cfg.j2', config=config)))
    resources.append(component_resource(name=config.driver))
    return resources


def load_database_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
        'driver', 'type', 'host', 'port', 'database', 'user', 'password', 'schema')
    config.port = int(config.port)
    return config