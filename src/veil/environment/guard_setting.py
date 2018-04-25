from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def guard_program(crontab_expression, redis_snapshot_shipping_config=None):
    program_config = objectify({
        'guard': {
            'execute_command': "veil environment backup guard-up '{}'".format(crontab_expression),
            'run_as': 'root',
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.environment.backup'
            })]
        }
    })
    if redis_snapshot_shipping_config:
        program_config['redis_snapshot_shipping'] = {
            'execute_command': 'veil environment backup snapshot-shipping {} {}'.format(','.join(redis_snapshot_shipping_config.purposes),
                                                                                        redis_snapshot_shipping_config.remote_path),
        }
    return program_config
