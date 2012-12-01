from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.utility.setting import *
from veil.environment import *

def website_programs(
        purpose, logging_levels, application_component_names, application_config,
        start_port, processes_count=1):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-website-log.cfg'.format(purpose)
    resources = [
        veil_logging_level_config_resource(
            path=veil_logging_level_config_path,
            logging_levels=logging_levels),
        application_resource(component_names=application_component_names, config=application_config)]
    additional_args = []
    for component in application_component_names:
        additional_args.append('--component {}'.format(component))
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
                'reloads_on_change': application_component_names,
                'group': '{}_website'.format(purpose),
            }
        })
    return programs


def website_upstreams(purpose, start_port, processes_count):
    return {
        '{}-tornado'.format(purpose):
            [{
                 'host': '127.0.0.1', # nginx and tornado has to live side by side, as they share upload/static files
                 'port': start_port + i
             } for i in range(processes_count)]
    }


def website_locations(purpose):
    return {
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
                proxy_pass http://%s-tornado;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                """ % (
                VEIL_VAR_DIR / 'uploaded-files',
                purpose),
        },
        '@after_upload': {
            'proxy_pass': 'http://{}-tornado'.format(purpose)
        },
        # inline static files
        # /static/v-xxxx/a-b.js
        '~ ^/static/v-(.*)/': {
            'alias': VEIL_VAR_DIR / 'inline-static-files' / '$1',
            'expires': '365d'
        },
        '/static/': {
            '_': """
                if ($args ~* v=(.+)) {
                    expires 365d;
                }
                """,
            'alias': VEIL_HOME / 'static' / ''
        }
    }