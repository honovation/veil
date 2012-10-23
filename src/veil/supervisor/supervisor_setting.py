from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.environment import *
from veil.model.collection import *

def supervisor_settings(**updates):
    settings = {
        'programs': {},
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        },
        'inet_http_server': {
            'host': '127.0.0.1',
            'port': 9090
        }
    }
    settings = merge_settings(settings, updates, overrides=True)
    return objectify({'supervisor': settings})
