from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def nginx_program():
    return objectify({
        'nginx': {
            'execute_command': 'nginx -c {}'.format(VEIL_ETC_DIR / 'nginx.conf'),
            'run_as': 'root',
            'installer_providers': ['veil.frontend.nginx'],
            'resources': [('nginx', {'servers': {}})]
        }
    })