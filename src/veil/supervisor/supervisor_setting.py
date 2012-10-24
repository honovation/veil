from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.environment import *
from veil.model.collection import *
from veil.frontend.nginx import *

def supervisor_settings(**updates):
    settings = {
        'programs': {},
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        },
        'inet_http_server': {
            'host': '127.0.0.1',
            'domain': 'supervisor.dev.dmright.com',
            'domain_port': 80,
            'port': 9090
        }
    }
    settings = merge_settings(settings, updates, overrides=True)
    return objectify({'supervisor': settings})


def add_supervisor_reverse_proxy_server(settings):
    settings = merge_settings(supervisor_settings(), settings, overrides=True)
    inet_http_server_config = settings.supervisor.inet_http_server
    server_name = inet_http_server_config.domain
    return merge_settings(settings, nginx_server_settings(settings, server_name,
        listen=int(inet_http_server_config.domain_port),
        locations={
            '/': {
                '_': """
                        proxy_pass http://%s:%s;
                        proxy_set_header   Host             $host;
                        proxy_set_header   X-Real-IP        $remote_addr;
                        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                        """ % (
                    inet_http_server_config.host,
                    inet_http_server_config.port),
            },
        }
    ))
