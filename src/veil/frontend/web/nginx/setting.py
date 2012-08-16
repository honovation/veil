from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *
from veil.environment.setting import *

def nginx_program():
    return {
        'command': 'veil frontend web nginx up',
        'user': 'root'
    }


def nginx_settings(**updates):
    settings = {
        'owner': CURRENT_USER,
        'owner_group': CURRENT_USER_GROUP,
        'log_directory': VEIL_LOG_DIR / 'nginx',
        'config_file': VEIL_ETC_DIR / 'nginx.conf',
        'uploaded_files_directory': VEIL_VAR_DIR / 'uploaded-files',
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static',
        'servers': {}
    }
    settings.update(updates)
    return objectify({'nginx': settings})


def add_reverse_proxy_server(settings, server_name, backend_host, backend_port, **updates):
    server_settings = {
        'listen': '127.0.0.1:80',
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
                    backend_host,
                    backend_port),
                },
            '@after_upload': {
                'proxy_pass': 'http://{}:{}'.format(backend_host, backend_port)
            },
            # inline static files
            # /static/v-xxxx/a-b.js
            '~ ^/static/v-(.*)/': {
                'alias': settings.nginx.inline_static_files_directory / '$1',
                'expires': '365d'
            },
            # external static files
            # /static/a/b/c.js?v=xxxx
            '/static/': {
                '_': """
                        if ($args ~* v=(.+)) {
                            expires 365d;
                        }
                        """,
                'alias': settings.nginx.external_static_files_directory / ''
            }
        }
    }
    if updates:
        server_settings = merge_settings(server_settings, updates)
    settings.nginx.servers[server_name] = server_settings


def copy_nginx_settings_to_veil(settings):
    if 'nginx' not in settings:
        return settings
    return merge_settings(settings, {
        'veil': {
            'website': {
                'inline_static_files_directory': settings.nginx.inline_static_files_directory,
                'external_static_files_directory': settings.nginx.external_static_files_directory,
                }
        }
    }, overrides=True)