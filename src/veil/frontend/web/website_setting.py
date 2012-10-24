from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from veil.frontend.nginx import *
from .website_program import website_program


def website_settings(website, port, **updates):
    port = int(port)
    if 'test' == VEIL_ENV:
        port += 1
    settings = objectify({
        'domain': '{}.dev.dmright.com'.format(website),
        'domain_port': 80,
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static',
        'host': 'localhost',
        'port': port
    })
    settings = merge_settings(settings, updates, overrides=True)
    if 'test' == VEIL_ENV:
        settings.domain_port = int(settings.domain_port) + 1
    return objectify({
        'veil': {'{}_website'.format(website): settings},
        'supervisor': {
            'programs': {
                '{}_website'.format(website): website_program(website)
            }
        } if 'test' != VEIL_ENV else {}
    })

def add_website_reverse_proxy_servers(settings):
    new_settings = settings
    for key, value in settings.veil.items():
        if key.endswith('_website'):
            website = key.replace('_website', '')
            reverse_proxy_server_settings = nginx_reverse_proxy_server_settings(settings, website)
            new_settings = merge_settings(new_settings, reverse_proxy_server_settings)
    return new_settings

