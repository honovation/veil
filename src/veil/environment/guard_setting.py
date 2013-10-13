from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def guard_program(crontab_expression, backup_mirror_host_user=None, backup_mirror_host_ip=None, backup_mirror_host_port=22, bandwidth_limit=3000):
    """
    bandwidth_limit: default 3000KB/s
    """
    return objectify({
        'guard': {
            'execute_command': "veil environment backup guard-up '{}'".format(crontab_expression),
            'run_as': 'root',
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.environment.backup'
            })]
        },
        'backup_mirror_host_user': backup_mirror_host_user,
        'backup_mirror_host_ip': backup_mirror_host_ip,
        'backup_mirror_host_port': backup_mirror_host_port,
        'backup_mirror_host_string': '{}@{}:{}'.format(backup_mirror_host_user, backup_mirror_host_ip, backup_mirror_host_port) if (backup_mirror_host_user and backup_mirror_host_ip and backup_mirror_host_port) else None,
        'bandwidth_limit': bandwidth_limit
    })