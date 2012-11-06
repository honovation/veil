from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *
from veil.environment.setting import *
from veil.utility.path import *

def nginx_program(**updates):
    settings = {
        'execute_command': 'veil frontend nginx up',
        'user': 'root',
        'installer_providers': ['veil.frontend.nginx'],
        'resources': [('nginx', {})]
    }
    return merge_settings(settings, updates)


def nginx_settings(**updates):
    settings = {
        'owner': CURRENT_USER,
        'owner_group': CURRENT_USER_GROUP,
        'log_directory': VEIL_LOG_DIR / 'nginx',
        'config_file': VEIL_ETC_DIR / 'nginx.conf',
        'pid_file': VEIL_VAR_DIR / 'nginx.pid',
        'uploaded_files_directory': VEIL_VAR_DIR / 'uploaded-files',
        'servers': {}
    }
    settings.update(updates)
    return objectify({
        'nginx': settings,
        'supervisor': {
            'programs': {
                'nginx': nginx_program()
            }
        }
    })


def nginx_server_settings(settings, server_name, **server_settings):
    if not getattr(settings, 'nginx', None):
        settings = merge_settings(settings, nginx_settings())
    return merge_settings(settings, objectify({
        'nginx': {
            'servers': {
                server_name: server_settings
            }
        }
    }))


def nginx_server_static_file_location_settings(settings, server_name, url_pattern, directory):
    if not getattr(settings, 'nginx', None):
        settings = merge_settings(settings, nginx_settings())
    location_settings = objectify({
        'nginx': {
            'servers': {
                server_name: {
                    'locations': {
                        url_pattern: {
                            '_': """
                            if ($args ~* v=(.+)) {
                                expires 365d;
                            }
                            """,
                            'alias': as_path(directory) / ''
                        }
                    }
                }
            }
        }
    })
    return merge_settings(settings, location_settings)



