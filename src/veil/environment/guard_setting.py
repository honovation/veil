from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def guard_program(crontab_expression):
    return objectify({
        'guard': {
            'execute_command': "veil environment backup guard-up {} '{}'".format(crontab_expression),
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.environment.backup'
            })]
        }
    })