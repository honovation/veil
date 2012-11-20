from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.model.collection import *

def website_program(purpose, dependencies, installer_providers, resources):
    resources = list(resources)
    additional_args = []
    for dependency in dependencies:
        resources.append(component_resource(dependency))
        additional_args.append('--dependency {}'.format(dependency))
    return objectify({
        '{}_website'.format(purpose): {
            'execute_command': 'veil frontend web up {} {}'.format(
                purpose, ' '.join(additional_args)),
            'installer_providers': installer_providers,
            'resources': resources,
            'reloads_on_change': True
        }
    })


def website_resource(purpose, domain, domain_port, host, port, secure_cookie_salt, master_template_directory,
                     prevents_xsrf, recalculates_static_file_hash, clears_template_cache):
    return 'website', {
        'purpose': purpose,
        'config': {
            'domain': domain,
            'domain_port': domain_port,
            'host': host,
            'port': port,
            'secure_cookie_salt': secure_cookie_salt,
            'master_template_directory': master_template_directory,
            'prevents_xsrf': prevents_xsrf,
            'recalculates_static_file_hash': recalculates_static_file_hash,
            'clears_template_cache': clears_template_cache
        }
    }


def website_locations(host, port):
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
                proxy_pass http://%s:%s;
                proxy_set_header   Host             $host;
                proxy_set_header   X-Real-IP        $remote_addr;
                proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                """ % (
                VEIL_VAR_DIR / 'uploaded-files',
                host, port),
        },
        '@after_upload': {
            'proxy_pass': 'http://{}:{}'.format(host, port)
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