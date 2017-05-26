from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.server.certbot_setting import certbot_program

NGINX_PID_PATH = '/tmp/nginx.pid'


def nginx_program(servers, enable_compression=False, base_domain_names=(), has_bunker=False, is_bunker=False,
                  bunker_ip=None, certbot_crontab_expression=None, **kwargs):
    assert len([name for name, properties in servers.items() if properties['default_server']]) <= 1
    settings = objectify({
        'nginx': {
            'execute_command': 'nginx -c {}'.format(VEIL_ETC_DIR / 'nginx.conf'),
            'run_as': 'root',
            'priority': 400,
            'resources': [('veil.frontend.nginx.nginx_resource', {
                'servers': servers,
                'config': dict({
                    'enable_compression': enable_compression,
                    'base_domain_names': base_domain_names,
                    'has_bunker': has_bunker,
                    'is_bunker': is_bunker,
                    'bunker_ip': bunker_ip
                }, **kwargs)
            })],
            'stopsignal': 'QUIT',
            'stopwaitsecs': 20
        }
    })
    if any(properties['use_certbot'] for properties in servers.values()):
        assert certbot_crontab_expression
        settings.update(certbot_program(certbot_crontab_expression))
    return settings


def nginx_server(server_name, listen, locations, upstreams=None, error_page=None, error_page_dir=None, ssl=False,
                 use_certbot=False, default_server=False, additional_listens=(), **kwargs):
    assert not use_certbot or ssl
    return {
        server_name: dict({
            'listen': int(listen),
            'additional_listens': tuple(int(listen) for listen in additional_listens),
            'locations': locations,
            'upstreams': upstreams,
            'error_page': error_page,
            'error_page_dir': error_page_dir,
            'ssl': ssl,
            'use_certbot': use_certbot,
            'default_server': default_server
        }, **kwargs)
    }


def nginx_reverse_proxy_location(upstream_host, upstream_port):
    return {
        '_': '''
            proxy_pass http://{}:{};
            '''.format(upstream_host, upstream_port)
    }
