from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def log_rotater_program(log_rotater_name, crontab_expression, config, run_as_current_user=False):
    config['config_file'] = VEIL_ETC_DIR / '{}-log-rotater.cfg'.format(log_rotater_name.replace('_', '-'))
    return objectify({
        '{}_log_rotater'.format(log_rotater_name): {
            'execute_command': "veil backend log-rotater up {} '{}'".format(config['config_file'], crontab_expression),
            'run_as': CURRENT_USER if run_as_current_user else 'root',
            'resources': [('veil.backend.log_rotater.log_rotater_resource', {
                'config': config
            })]
        }
    })
