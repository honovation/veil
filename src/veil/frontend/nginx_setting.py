from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def nginx_program(servers):
    return objectify({
        'nginx': {
            'execute_command': 'nginx -c {}'.format(VEIL_ETC_DIR / 'nginx.conf'),
            'run_as': 'root',
            'resources': [('veil.frontend.nginx.nginx_resource', {'servers': servers})]
        }
    })


def nginx_server(server_name, listen, locations, upstreams=None):
    return {
        server_name: {
            'listen': listen,
            'locations': locations,
            'upstreams': upstreams
        }
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
