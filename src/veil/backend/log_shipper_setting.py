from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def log_shipper_program(log_file_path, redis_key):
    return objectify({
        'log_shipper': {
            'execute_command': 'veil backend log-shipper up {} {}'.format(log_file_path, redis_key),
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.backend.log_shipper'
            })]
        }
    })