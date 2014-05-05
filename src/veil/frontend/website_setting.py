from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.utility.setting import *
from veil.environment import *
from veil.server.python import *
from veil_component import *


def website_programs(purpose, logging_levels, application_config, start_port, processes_count=1):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-website-log.cfg'.format(purpose)
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=logging_levels),
        component_resource(name='veil.profile.web'),
        application_resource(component_names=list_website_components(purpose), config=application_config)
    ]
    additional_args = []
    programs = {}
    for i in range(processes_count):
        programs = merge_settings(programs, {
            '{}_tornado{}'.format(purpose, i + 1): {
                'execute_command': 'veil frontend web up {} {} {}'.format(purpose, start_port + i, ' '.join(additional_args)),
                'environment_variables': {'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path, 'VEIL_LOGGING_EVENT': 'True'},
                'redirect_stderr': False,
                'resources': resources,
                'group': '{}_website'.format(purpose),
                'patchable': True
            }
        })
    return programs


def list_website_components(website):
    return list_dynamic_dependency_providers('website', website.lower())


def website_upstreams(purpose, start_port, processes_count):
    return {'{}-tornado'.format(purpose): [{
        'host': '127.0.0.1',  # nginx and tornado has to live side by side, as they share upload/static files
        'port': start_port + i
    } for i in range(processes_count)]}


def website_locations(purpose, has_bunker=False, is_api_only=False, max_upload_file_size='1m', extra_headers=None):
    if is_api_only:
        return {'/': {
            '_': '''
                proxy_pass http://{}-tornado;
                {}
                '''.format(purpose, extra_headers or '')
        }}

    extra_headers = '''
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-UA-Compatible "IE=Edge,chrome=1";
        {}
        '''.format(extra_headers or '')
    if has_bunker:
        # done in bunker
        extra_locations = {}
    else:
        extra_locations = {
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
            '/static/': {
                '_': '''
                    alias {}/static/;
                    access_log off;
                    expires max;
                    if ($query_string !~ "v=.+") {{
                        expires 4h;
                    }}
                    '''.format(VEIL_HOME)
            }
        }
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
            '''.format(max_upload_file_size, VEIL_VAR_DIR / 'uploaded-files', purpose, extra_headers)
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
        # /static/v-xxxx/a-b.js
        '~ ^/static/v-(.*)-(.*)/': {
            '_': '''
                alias {}/inline-static-files/$1/$2;
                access_log off;
                expires max;
                '''.format(VEIL_VAR_DIR)
        }
    }
    locations.update(extra_locations)
    return locations
