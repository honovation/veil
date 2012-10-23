from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from .website import website_program

def website_settings(website, port, **updates):
    port = int(port)
    if 'test' == VEIL_ENV:
        port += 1
    settings = objectify({
        'domain': '{}.dev.dmright.com'.format(website),
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static',
        'host': 'localhost',
        'port': port
    })
    settings = merge_settings(settings, updates, overrides=True)
    return objectify({
        'veil': {'{}_website'.format(website): settings},
        'supervisor': {
            'programs': {
                '{}_website'.format(website): website_program(website)
            }
        } if 'test' != VEIL_ENV else {}
    })

