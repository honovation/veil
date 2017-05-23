# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def certbot_program(crontab_expression):
    return objectify({
        'certbot': {
            'execute_command': "veil server certbot renew-termly '{}'".format(crontab_expression),
            'run_as': 'root',
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.server.certbot'
            })]
        }
    })
