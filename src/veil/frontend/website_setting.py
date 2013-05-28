from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.utility.setting import *
from veil.environment import *
from veil.server.python import *
from veil_component import *

def website_programs(purpose, logging_levels, application_config, start_port, processes_count=1):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-website-log.cfg'.format(purpose)
    resources = [
        veil_logging_level_config_resource(
            path=veil_logging_level_config_path,
            logging_levels=logging_levels),
        application_resource(component_names=list_website_components(purpose), config=application_config)]
    additional_args = []
    programs = {}
    for i in range(processes_count):
        programs = merge_settings(programs, {
            '{}_tornado{}'.format(purpose, i + 1): {
                'execute_command': 'veil frontend web up {} {} {}'.format(
                    purpose, start_port + i, ' '.join(additional_args)),
                'environment_variables': {
                    'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                    'VEIL_LOGGING_EVENT': 'True'
                },
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
    return {
        '{}-tornado'.format(purpose):
            [{
                 'host': '127.0.0.1', # nginx and tornado has to live side by side, as they share upload/static files
                 'port': start_port + i
             } for i in range(processes_count)]
    }


def website_locations(purpose):
    if VEIL_ENV in {'ljmall-public', 'ljmall-staging'}:
        # done in bunker
        extra_headers = ''
        extra_locations = {}
    else:
        extra_headers = '''
            add_header X-Frame-Options SAMEORIGIN;
            add_header X-UA-Compatible "IE=Edge,chrome=1";
            '''
        extra_locations = {
            '= /favicon.ico': {
                '_': '''
                    access_log off; log_not_found off;
                    expires 60d;
                    ''',
                'alias': VEIL_HOME / 'static' / 'favicon.ico'
            },
            '= /robots.txt': {
                '_': '''
                    access_log off; log_not_found off;
                    ''',
                'alias': VEIL_HOME / 'static' / '{}-robots.txt'.format(purpose)
            },
            '/static/': {
                '_': '''
                    access_log off;
                    expires max;
                    if ($query_string !~* "v=(.+)") {
                        expires 7d;
                        add_header Pragma public;
                        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
                    }
                    ''',
                'alias': VEIL_HOME / 'static' / ''
            }
        }
    locations = {
        '= /': {
            '_': '''
                proxy_pass http://%s-tornado;
                proxy_redirect off;
                proxy_next_upstream error;
                %s
                ''' % (purpose, extra_headers)
        },
        '/': {
            '_': '''
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
                proxy_pass http://%s-tornado;
                proxy_redirect off;
                proxy_next_upstream error;
                %s
                ''' % (VEIL_VAR_DIR / 'uploaded-files', purpose, extra_headers)
        },
        '@after_upload': {
            'proxy_pass': 'http://{}-tornado'.format(purpose)
        },
        # inline static files
        # /static/v-xxxx/a-b.js
        '~ ^/static/v-(.*)/': {
            'alias': VEIL_VAR_DIR / 'inline-static-files' / '$1',
            'access_log': 'off',
            'expires': 'max'
        }
    }
    locations.update(extra_locations)
    return locations;
