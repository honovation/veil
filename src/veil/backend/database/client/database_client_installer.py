from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('database_client')
@using_isolated_template
def install_database_client(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')), content=get_template(
        'database-client.cfg.j2').render(config=config)))
    resources.append(component_resource(config.driver))
    return [], resources


def load_database_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
        'driver', 'type', 'host', 'port', 'database', 'user', 'password', 'schema')
    config.port = int(config.port)
    return config