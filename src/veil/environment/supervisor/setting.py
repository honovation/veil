from __future__ import unicode_literals, print_function, division
from ..layout import VEIL_ETC_DIR, VEIL_LOG_DIR


SUPERVISOR_BASE_SETTINGS = {
    'supervisor': {
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
}