from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = {}


@composite_installer
def database_client_resource(purpose, config):
    return [
        file_resource(path=VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')),
                      content=render_config('database-client.cfg.j2', config=config), owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        component_resource(name=config.driver)
    ]


def load_database_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-database-client.cfg'.format(purpose.replace('_', '-')), 'driver', 'type', 'host', 'port', 'database', 'user',
                              'password')
    config.port = int(config.port)
    config.schema = config.get('schema')
    config.enable_chinese_fts = config.get('enable_chinese_fts', '0') == '1'
    config.enable_modules = config['enable_modules'].split(',') if 'enable_modules' in config else []
    return config


def database_client_config(purpose):
    return _config.setdefault(purpose, load_database_client_config(purpose))
