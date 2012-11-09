from __future__ import unicode_literals, print_function, division
from veil.environment import *

def source_code_monitor_settings():
    if 'development' != VEIL_SERVER:
        return {}
    return {
        'supervisor': {
            'programs': {
                'source_code_monitor': {
                    'execute_command': 'veil development source-code-monitor up',
                    'startsecs': 0,
                    'user': 'root' # required to clear pyc files
                }
            }
        }
    }