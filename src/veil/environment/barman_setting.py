# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def barman_periodic_backup_program(crontab_expression, purpose):
    return objectify({
        'barman_backup': {
            'execute_command': 'veil environment backup barman-backup "{}" {}'.format(crontab_expression, purpose)
        }
    })


def barman_periodic_recover_program(crontab_expression, purpose):
    return objectify({
        'barman_recover': {
            'execute_command': 'veil environment backup barman-recover "{}" {}'.format(crontab_expression, purpose)
        }
    })
