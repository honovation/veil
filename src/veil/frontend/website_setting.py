from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def website_programs(purpose, logging_levels, application_config, start_port, process_count=1):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-website-log.cfg'.format(purpose)
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=logging_levels),
        component_resource(name='veil.profile.web'),
        application_resource(component_names=list_website_components(purpose), config=application_config)
    ]
    programs = {}
    for i in range(process_count):
        programs = merge_settings(programs, {
            '{}_tornado{}'.format(purpose, i + 1): {
                'execute_command': 'veil frontend web up {} {}'.format(purpose, start_port + i),
                'environment_variables': {'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path, 'VEIL_LOGGING_EVENT': 'True'},
                'priority': 300,
                'redirect_stderr': False,
                'resources': resources,
                'group': '{}_website'.format(purpose),
                'patchable': True
            }
        })
    return programs


def list_website_components(website):
    return list_dynamic_dependency_providers('website', website.lower())


def website_upstreams(purpose, start_port, process_count):
    return {'{}-tornado'.format(purpose): [{
        'host': '127.0.0.1',  # nginx and tornado has to live side by side, as they share upload/static files
        'port': start_port + i
    } for i in range(process_count)]}


def website_locations(purpose, has_bunker=False, is_api_only=False, intranet_cidr_list=None, max_upload_file_size='1m', extra_headers=(), extra_locations=None,
                      valid_referer_domains=None):
    if is_api_only:
        common_setting = '''
            proxy_pass http://{}-tornado;
            {}
            '''.format(purpose, '\n'.join(extra_headers))
        if intranet_cidr_list:
            intranet_only = '''
                {}
                deny all;
                '''.format('\n'.join('allow {};'.format(intranet_cidr) for intranet_cidr in intranet_cidr_list))
            locations = {
                '^~ /pn/': {
                    '_': '''
                        if ($scheme = "http") {{ return 403; }}
                        {}
                        '''.format(common_setting)
                },
                '/': {
                    '_': '''
                        {}
                        {}
                        '''.format(intranet_only, common_setting)
                }
            }
        else:
            locations = {
                '/': {
                    '_': '''
                        {}
                        '''.format(common_setting)
                }
            }
        return locations

    extra_headers = '''
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-XSS-Protection "1; mode=block";
        add_header X-UA-Compatible "IE=Edge,chrome=1";
        {}
        '''.format('\n'.join(extra_headers))
    if valid_referer_domains:
        stop_referring = '''
            valid_referers none blocked {};
            if ($invalid_referer) {{
                return 403;
            }}
            '''.format(valid_referer_domains)
    else:
        stop_referring = ''
    extra_locations = extra_locations or {}
    if not has_bunker:
        extra_locations.update({
            '= /favicon.ico': {
                '_': '''
                    access_log off; log_not_found off;
                    expires 1M;
                    ''',
                'alias': VEIL_HOME / 'static' / purpose / 'favicon.ico'
            },
            '= /robots.txt': {
                '_': '''
                    access_log off; log_not_found off;
                    expires 1h;
                    ''',
                'alias': VEIL_HOME / 'static' / purpose / 'robots.txt'
            },
            '~ ^/static/images/(logo.*\.gif)$': {
                '_': '''
                    set $logo_file $1;
                    alias {}/static/images/$logo_file;
                    access_log off;
                    expires max;
                    if ($query_string !~ "v=.+") {{
                        expires 4h;
                    }}
                    '''.format(VEIL_HOME)
            },
            '/static/': {
                '_': '''
                    {}
                    alias {}/static/;
                    access_log off;
                    expires max;
                    if ($query_string !~ "v=.+") {{
                        expires 4h;
                    }}
                    '''.format(stop_referring, VEIL_HOME)
            }
        })
    locations = {
        '= /': {
            '_': '''
                proxy_pass http://{}-tornado;
                {}
                '''.format(purpose, extra_headers)
        },
        '^~ /fupload/': {
            '_': '''
                client_max_body_size {};
                client_body_temp_path {} 1;
                client_body_in_file_only clean;
                proxy_set_header X-UPLOAD-FILE-PATH $request_body_file;
                proxy_set_body off;
                proxy_pass http://{}-tornado;
                {}
            '''.format(max_upload_file_size, VEIL_BUCKET_UPLOADED_FILES_DIR, purpose, extra_headers)
        },
        '^~ /fupload-/': {
            '_': '''
                client_max_body_size {};
                proxy_pass http://{}-tornado;
                {}
                '''.format(max_upload_file_size, purpose, extra_headers)
        },
        '/': {
            '_': '''
                proxy_pass http://{}-tornado;
                {}
                '''.format(purpose, extra_headers)
        },
        # inline static files
        # /static/v-xx-xx/a-b.js
        '~ ^/static/v-(.*)-(.*)/': {
            '_': '''
                {}
                alias {}/$1/$2;
                access_log off;
                expires max;
                '''.format(stop_referring, VEIL_BUCKET_INLINE_STATIC_FILES_DIR)
        }
    }
    locations.update(extra_locations)
    return locations
