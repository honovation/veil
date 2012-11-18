from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *

def website_program(
        purpose, host, port, secure_cookie_salt, master_template_directory,
        prevents_xsrf, recalculates_static_file_hash, clears_template_cache, dependencies):
    additional_args = []
    for dependency in dependencies:
        additional_args.append('--dependency {}'.format(dependency))
    return objectify({
        '{}_website'.format(purpose): {
            'execute_command': 'veil frontend web up {} {}'.format(
                purpose, ' '.join(additional_args)),
            'installer_providers': ['veil.frontend.web'],
            'resources': [('website', {
                'purpose': purpose,
                'config': {
                    'host': host,
                    'port': port,
                    'secure_cookie_salt': secure_cookie_salt,
                    'master_template_directory': master_template_directory,
                    'prevents_xsrf': prevents_xsrf,
                    'recalculates_static_file_hash': recalculates_static_file_hash,
                    'clears_template_cache': clears_template_cache
                },
                'dependencies': dependencies
            })],
            'reloads_on_change': True
        }
    })


def load_website_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}_website.cfg'.format(purpose),
        'host', 'port', 'secure_cookie_salt', 'master_template_directory',
        'prevents_xsrf', 'recalculates_static_file_hash', 'clears_template_cache')
    config.port = int(config.port)
    config.prevents_xsrf = unicode(True) == config.prevents_xsrf
    config.recalculates_static_file_hash = unicode(True) == config.recalculates_static_file_hash
    config.clears_template_cache = unicode(True) == config.clears_template_cache
    return config