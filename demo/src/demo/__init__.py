def init():
    from sandal.component import init_component
    from sandal.const import consts
    from sandal.event import subscribe_event
    from sandal.option import init_options
    from sandal.option import merge_options

    init_component(__name__)

    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    subscribe_event(consts.EVENT_ENVIRONMENT_INSTALLING, lambda options: init_options(merge_options(options, {
        'nginx': {
            'servers': {
                'demo.dev.dmright.com': {
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
                                options.nginx.uploaded_files_directory,
                                DEMO_WEB_HOST,
                                DEMO_WEB_PORT),
                        },
                        '@after_upload': {
                            'proxy_pass': 'http://{}:{}'.format(DEMO_WEB_HOST, DEMO_WEB_PORT)
                        },
                        # inline static files
                        # /static/v-xxxx/a-b.js
                        '~ ^/static/v-(.*)/': {
                            'alias': options.nginx.inline_static_files_directory / '$1',
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
                            'alias': options.nginx.external_static_files_directory / ''
                        }
                    }
                }
            }
        },
        'supervisor': {
            'programs': {
                'demo': {
                    'command': 'veil demo up'
                },
                'nginx': {
                    'command': 'nginx -c {{ config_file }}',
                    'args': {
                        'config_file': options.nginx.config_file
                    },
                    'user': 'root'
                }
            }
        }
    })))

init()