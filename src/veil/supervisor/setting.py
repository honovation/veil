from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *


SUPERVISOR_BASE_SETTINGS = {
    'supervisor': {
        'programs': {},
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
}