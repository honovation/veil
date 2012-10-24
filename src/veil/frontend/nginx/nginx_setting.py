from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *
from veil.environment.setting import *

def nginx_program(**updates):
    settings = {
        'execute_command': 'veil frontend nginx up',
        'install_command': 'veil frontend nginx install',
        'user': 'root'
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


def nginx_reverse_proxy_server_settings(settings, website, **updates):
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
    if updates:
        server_settings = merge_settings(server_settings, updates)
    # external static files
    # /static/a/b/c.js?v=xxxx
    static_location_settings = nginx_reverse_proxy_static_file_location_settings(
        settings, website, '/static/', website_config.external_static_files_directory)
    settings = merge_settings(settings, objectify({
        'nginx': {
            'servers': {
                website_config.domain: server_settings
            }
        }
    }))
    return merge_settings(settings, static_location_settings)


def nginx_reverse_proxy_static_file_location_settings(settings, website, url_pattern, directory):
    if not getattr(settings, 'nginx', None):
        settings = merge_settings(settings, nginx_settings())
    location_settings = objectify({
        'nginx': {
            'servers': {
                get_website_config(settings, website).domain: {
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


def get_website_config(settings, website):
    veil_config = getattr(settings, 'veil', None)
    if not veil_config:
        raise Exception('veil is not defined in settings')
    website_config = getattr(settings.veil, '{}_website'.format(website), None)
    if not website_config:
        raise Exception('website {} is not defined in settings'.format(website))
    return website_config
