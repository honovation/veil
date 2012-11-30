from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def remote_guard_program(backing_up_env, crontab_expression):
    return objectify({
        'remote_guard': {
            'execute_command': "veil environment remote-guard backup-env-at {} '{}'".format(
                backing_up_env, crontab_expression),
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.environment.remote_guard'
            })]
        }
    })