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
        }
    }
    settings = merge_settings(settings, updates, overrides=True)
    return objectify({'supervisor': settings})