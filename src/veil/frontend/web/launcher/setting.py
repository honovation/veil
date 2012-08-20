from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *

registry = {} # website => get_website_options

def website_settings(website, **updates):
    settings = objectify({
        'domain': '{}.dev.dmright.com'.format(website),
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static',
        'host': 'localhost'
    })
    settings = merge_settings(settings, updates)
    return {'veil': {'{}_website'.format(website): settings}}


def register_website(website):
    website = website.lower()
    if website not in registry:
        registry[website] = register_website_options(website)
    return registry[website]


def register_website_options(website):
    section = '{}_website'.format(website.lower()) # for example shopper_website
    get_reloads_module = register_option(section, 'reloads_module', bool, default=True)
    get_recalculates_static_file_hash = register_option(section, 'recalculates_static_file_hash', bool, default=True)
    get_clears_template_cache = register_option(section, 'clears_template_cache', bool, default=True)
    get_prevents_xsrf = register_option(section, 'prevents_xsrf', bool, default=True)
    get_master_template_directory = register_option(section, 'master_template_directory', default='')
    get_secure_cookie_salt = register_option(section, 'secure_cookie_salt', default='')
    get_host = register_option(section, 'host')
    get_port = register_option(section, 'port', int)
    get_processes_count = register_option(section, 'processes_count', default=1)
    get_inline_static_files_directory = register_option(section, 'inline_static_files_directory')
    get_external_static_files_directory = register_option(section, 'external_static_files_directory')
    get_domain = register_option(section, 'domain')

    def get_website_options():
        return {
            'reloads_module': get_reloads_module(),
            'recalculates_static_file_hash': get_recalculates_static_file_hash(),
            'clears_template_cache': get_clears_template_cache(),
            'prevents_xsrf': get_prevents_xsrf(),
            'master_template_directory': get_master_template_directory(),
            'secure_cookie_salt': get_secure_cookie_salt(),
            'host': get_host(),
            'port': get_port(),
            'processes_count': get_processes_count(),
            'inline_static_files_directory': get_inline_static_files_directory(),
            'external_static_files_directory': get_external_static_files_directory(),
            'domain': get_domain()
        }

    return get_website_options


def get_website_option(website, name):
    website = website.lower()
    return registry[website]()[name]

