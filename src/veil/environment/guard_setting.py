from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def guard_program(host_backup_crontab_expression='7 4 * * *', bucket_sync_config=None, redis_aof_sync_config=None):
    program_config = DictObject()
    if host_backup_crontab_expression:
        program_config['host_backup'] = {
            'execute_command': "veil environment backup host-backup '{}'".format(host_backup_crontab_expression),
            'resources': [('veil_installer.component_resource', {'name': 'veil.environment.backup'})]
        }
    if bucket_sync_config:
        program_config['bucket_sync'] = {
            'execute_command': 'veil environment backup bucket-sync {} {}'.format(','.join(bucket_sync_config.exclude_buckets), bucket_sync_config.remote_path),
            'resources': [('veil_installer.component_resource', {'name': 'veil.environment.backup'})]
        }
    if redis_aof_sync_config:
        program_config['redis_aof_sync'] = {
            'execute_command': "veil environment backup redis-aof-sync {} {} '{}'".format(','.join(redis_aof_sync_config.purposes),
                                                                                          redis_aof_sync_config.remote_path,
                                                                                          redis_aof_sync_config.crontab_expression),
            'resources': [('veil_installer.component_resource', {'name': 'veil.environment.backup'})]
        }
    return program_config
