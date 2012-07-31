from __future__ import unicode_literals, print_function, division

def ensure_veil_settings_consistent_with_dependencies(settings):
    return {
        'veil': {
            'website': {
                'inline_static_files_directory': settings.nginx.inline_static_files_directory,
                'external_static_files_directory': settings.nginx.external_static_files_directory,
            },
            'queue': {
                'host': settings.queue.bind,
                'port': settings.queue.port,
                'password': settings.queue.password
            }
        }
    }