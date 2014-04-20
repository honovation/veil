from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

NGINX_PID_PATH = VEIL_VAR_DIR / 'nginx.pid'

def nginx_program(servers, enable_compression=False, has_bunker=False, is_bunker=False, bunker_ip=None, **kwargs):
    return objectify({
        'nginx': {
            'execute_command': 'nginx -c {}'.format(VEIL_ETC_DIR / 'nginx.conf'),
            'run_as': 'root',
            'resources': [('veil.frontend.nginx.nginx_resource', {
                'servers': servers,
                'config': dict({
                    'enable_compression': enable_compression,
                    'has_bunker': has_bunker,
                    'is_bunker': is_bunker,
                    'bunker_ip': bunker_ip
                }, **kwargs)
            })]
        }
    })


def nginx_server(server_name, listen, locations, upstreams=None, error_page=None, error_page_dir=None, ssl=False, default_server=False, **kwargs):
    return {
        server_name: dict({
            'listen': '{}{}{}'.format(listen, ' ssl' if ssl else '', ' default_server' if default_server else ''),
            'locations': locations,
            'upstreams': upstreams,
            'error_page': error_page,
            'error_page_dir': error_page_dir
        }, **kwargs)
    }


def nginx_reverse_proxy_location(upstream_host, upstream_port):
    return {
        '_': '''
            proxy_pass http://{}:{};
            '''.format(upstream_host, upstream_port)
    }
