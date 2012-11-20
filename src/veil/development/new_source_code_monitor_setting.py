from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def source_code_monitor_program():
    return objectify({
        'source_code_monitor': {
            'execute_command': 'veil development source-code-monitor up',
            'startsecs': 0,
            'run_as': 'root' # required to clear pyc files
        }
    })