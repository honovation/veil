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


def nginx_server(server_name, listen, locations, ssl=False, use_certbot=False, default_server=False,
                 additional_http_listens=None, additional_https_listens=None, upstreams=None, error_page=None,
                 error_page_dir=None, **kwargs):
    assert ssl and listen != 80 or not ssl and listen != 443

    http_listens = additional_http_listens or []
    https_listens = additional_https_listens or []
    if ssl:
        https_listens.insert(0, listen)
    else:
        http_listens.insert(0, listen)

    assert http_listens or https_listens
    assert not use_certbot or https_listens

    return {
        server_name: dict({
            'http_listens': http_listens,
            'https_listens': https_listens,
            'ssl': ssl,
            'use_certbot': use_certbot,
            'default_server': default_server,
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
