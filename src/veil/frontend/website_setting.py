from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.nginx_setting import nginx_settings
from veil.frontend.nginx_setting import nginx_server_settings
from veil.frontend.nginx_setting import nginx_server_static_file_location_settings
from veil.model.collection import *
from veil.utility.path import *

def init():
    register_settings_coordinator(add_website_reverse_proxy_servers)

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


def website_program(website, **updates):
    program = {
        'execute_command': 'veil frontend web up {}'.format(website),
        'install_command': 'veil frontend web install {}'.format(website)
    }
    if updates:
        program.update(updates)
    return program


def add_website_reverse_proxy_servers(settings):
    new_settings = settings
    for key, value in settings.veil.items():
        if key.endswith('_website'):
            website = key.replace('_website', '')
            reverse_proxy_server_settings = nginx_reverse_proxy_server_settings(settings, website)
            new_settings = merge_settings(new_settings, reverse_proxy_server_settings)
    return new_settings


def nginx_reverse_proxy_server_settings(settings, website):
    if not getattr(settings, 'nginx', None):
        settings = merge_settings(settings, nginx_settings())
    website_config = get_website_config(settings, website)
    server_settings = {
        'listen': int(website_config.domain_port),
        'locations': {
            '/': {
                '_': """
                        if ($content_type ~* multipart/form-data) {
                            upload_pass @after_upload;
                            upload_store %s 1;
                            upload_set_form_field $upload_field_name.name "$upload_file_name";
                            upload_set_form_field $upload_field_name.content_type "$upload_content_type";
                            upload_set_form_field $upload_field_name.path "$upload_tmp_path";
                            upload_pass_args on;
                            upload_pass_form_field "^.*$";
                            upload_cleanup 400-599;
                            break;
                        }
                        proxy_pass http://%s:%s;
                        proxy_set_header   Host             $host;
                        proxy_set_header   X-Real-IP        $remote_addr;
                        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                        """ % (
                    settings.nginx.uploaded_files_directory,
                    website_config.host,
                    website_config.port),
            },
            '@after_upload': {
                'proxy_pass': 'http://{}:{}'.format(website_config.host, website_config.port)
            },
            # inline static files
            # /static/v-xxxx/a-b.js
            '~ ^/static/v-(.*)/': {
                'alias': as_path(website_config.inline_static_files_directory) / '$1',
                'expires': '365d'
            }
        }
    }
    # external static files
    # /static/a/b/c.js?v=xxxx
    static_location_settings = nginx_server_static_file_location_settings(
        settings, website_config.domain, '/static/', website_config.external_static_files_directory)
    settings = nginx_server_settings(settings, website_config.domain, **server_settings)
    return merge_settings(settings, static_location_settings)


def get_website_nginx_server_name(settings, website):
    return get_website_config(settings, website).domain


def get_website_config(settings, website):
    veil_config = getattr(settings, 'veil', None)
    if not veil_config:
        raise Exception('veil is not defined in settings')
    website_config = getattr(settings.veil, '{}_website'.format(website), None)
    if not website_config:
        raise Exception('website {} is not defined in settings'.format(website))
    return website_config

init()