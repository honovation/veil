from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *
from veil.environment.setting import *

def nginx_program(**updates):
    settings = {
        'command': 'veil frontend web nginx up',
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


def add_reverse_proxy_server(settings, website, **updates):
    website_config = getattr(settings.veil, '{}_website'.format(website))
    if ':' in website_config.domain:
        server_name, listen_port = website_config.domain.split(':')
    else:
        server_name, listen_port = website_config.domain, 80
    listen_port = int(listen_port)
    if 'test' == VEIL_ENV and not website_config.get('domain_modified_due_to_test_env', False):
        listen_port += 1
    website_config.domain = '{}:{}'.format(server_name, listen_port)
    website_config.domain_modified_due_to_test_env = True
    server_settings = {
        'listen': listen_port,
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
            },
            # external static files
            # /static/a/b/c.js?v=xxxx
            '/static/': {
                '_': """
                        if ($args ~* v=(.+)) {
                            expires 365d;
                        }
                        """,
                'alias': as_path(website_config.external_static_files_directory) / ''
            }
        }
    }
    if updates:
        server_settings = merge_settings(server_settings, updates)
    settings.nginx.servers[server_name] = server_settings
    return settings