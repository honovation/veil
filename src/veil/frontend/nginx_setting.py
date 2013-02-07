from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

NGINX_PID_PATH = VEIL_VAR_DIR / 'nginx.pid'

def nginx_program(servers, enable_compression=False):
    return objectify({
        'nginx': {
            'execute_command': 'nginx -c {}'.format(VEIL_ETC_DIR / 'nginx.conf'),
            'run_as': 'root',
            'resources': [('veil.frontend.nginx.nginx_resource', {
                'servers': servers,
                'enable_compression': enable_compression
            })]
        }
    })


def nginx_server(server_name, listen, locations, upstreams=None, error_page=None, error_page_dir=None, default_server=False, **kwargs):
    return {
        server_name: dict({
            'listen': '{}{}'.format(listen, ' default_server' if default_server else ''),
            'locations': locations,
            'upstreams': upstreams,
            'error_page': error_page,
            'error_page_dir': error_page_dir
        }, **kwargs)
    }


def nginx_reverse_proxy_location(upstream_host, upstream_port):
    return {
        '_': """
            proxy_pass http://%s:%s;
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
            """ % (upstream_host, upstream_port)
    }
