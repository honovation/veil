from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOG_ROTATER_CONF_PATH = VEIL_ETC_DIR / 'log-rotater.cfg'

def log_rotater_program(crontab_expression, config):
    return objectify({
        'log_rotater': {
            'execute_command': "veil backend log-rotater up '{}'".format(crontab_expression),
            'run_as': 'root',
            'resources': [('veil.backend.log_rotater.log_rotater_resource', {
                'config': config
            })]
        }
    })