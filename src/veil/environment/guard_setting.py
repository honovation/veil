from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def guard_program(crontab_expression, redis_aof_shipping_config=None, bucket_shipping_config=None):
    program_config = objectify({
        'guard': {
            'execute_command': "veil environment backup guard-up '{}'".format(crontab_expression),
            'run_as': 'root',
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.environment.backup'
            })]
        }
    })
    if redis_aof_shipping_config:
        program_config['redis_snapshot_shipping'] = {
            'execute_command': 'veil environment backup snapshot-shipping {} {} {}'.format(','.join(redis_aof_shipping_config.purposes),
                                                                                           redis_aof_shipping_config.remote_path,
                                                                                           redis_aof_shipping_config.crontab_expression),
            'run_as': 'root'
        }
    if bucket_shipping_config:
        program_config['bucket_shipping'] = {
            'execute_command': 'veil environment backup bucket-shipping {} {}'.format(','.join(bucket_shipping_config.exclude_buckets),
                                                                                      bucket_shipping_config.remote_path),
            'run_as': 'root'
        }
    return program_config
