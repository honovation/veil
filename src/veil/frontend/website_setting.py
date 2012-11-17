from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.nginx_setting import nginx_settings
from veil.frontend.nginx_setting import nginx_server_settings
from veil.frontend.nginx_setting import nginx_server_static_file_location_settings
from veil.model.collection import *
from veil.utility.path import *
from veil.development.source_code_monitor_setting import source_code_monitor_settings
from veil.development.self_checker_setting import self_checker_settings

def init():
    register_settings_coordinator(add_website_reverse_proxy_servers)


def website_settings(purpose, port, dependencies, **updates):
    return merge_multiple_settings(
        _website_settings(purpose, port, dependencies, **updates),
        _website_settings('test', 5090, []) if 'test' == VEIL_ENV else {},
        source_code_monitor_settings(),
        self_checker_settings())


def _website_settings(purpose, port, dependencies, **updates):
    port = int(port)
    if 'test' == VEIL_ENV:
        port += 1
    settings = objectify({
        'domain': '{}.dev.dmright.com'.format(purpose),
        'domain_port': 80,
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static',
        'host': 'localhost',
        'port': port
    })
    settings = merge_settings(settings, updates, overrides=True)
    if 'test' == VEIL_ENV:
        settings = merge_settings(settings, {
            'domain_port': int(settings.domain_port) + 1
        }, overrides=True)
    return objectify({
        '{}_website'.format(purpose): settings,
        'supervisor': {
            'programs': {
                '{}_website'.format(purpose): website_program(purpose, dependencies)
            }
        } if 'test' != VEIL_ENV else {}
    })


def get_website_options(purpose):
    config = get_settings()['{}_website'.format(purpose)]
    return objectify({
        'recalculates_static_file_hash': config.get('recalculates_static_file_hash', True),
        'clears_template_cache': config.get('clears_template_cache', True),
        'prevents_xsrf': config.get('prevents_xsrf', True),
        'master_template_directory': config.get('master_template_directory', ''),
        'secure_cookie_salt': config.get('secure_cookie_salt', ''),
        'host': config.host,
        'port': config.port,
        'processes_count': config.get('processes_count', 1),
        'inline_static_files_directory': config.inline_static_files_directory,
        'external_static_files_directory': config.external_static_files_directory,
        'domain': config.domain,
        'domain_port': config.domain_port
    })


def get_website_url_prefix(purpose):
    website_options = get_website_options(purpose)
    return 'http://{}:{}'.format(website_options.domain, website_options.domain_port)


def website_program(website, dependencies):
    resources = [component_resource('veil.frontend.web')]
    for dependency in dependencies:
        resources.append(component_resource(dependency))
    program = {
        'execute_command': 'veil frontend web up {}'.format(website),
        'resources': resources,
        'reloads_on_change': True # used by source code monitor in development mode
    }
    return program


def add_website_reverse_proxy_servers(settings):
    new_settings = settings
    for key, value in settings.items():
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
    website_config = getattr(settings, '{}_website'.format(website), None)
    if not website_config:
        raise Exception('website {} is not defined in settings'.format(website))
    return website_config

init()