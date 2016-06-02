from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOG_SHIPPER_CONF_PATH = VEIL_ETC_DIR / 'log-shipper.cfg'


def log_shipper_program(config):
    return objectify({
        'log_shipper': {
            'execute_command': 'veil backend log-shipper up',
            'priority': 1,  # first to start to ship other programs startup logs
            'resources': [('veil.backend.log_shipper.log_shipper_resource', {'config': config})]
        }
    })
