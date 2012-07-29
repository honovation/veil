def init():
    from sandal.component import init_component
    from veil.environment.layout import VEIL_ENV
    from veil.environment.deployment import register_deployment_settings_provider
    from veil.web.nginx import create_nginx_server_settings
    from veil.web.nginx import NGINX_BASE_SETTINGS

    init_component(__name__)

    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    UNPRIVILIGED_USER = 'dejavu'
    UNPRIVILIGED_GROUP = 'dejavu'
    if 'test' == VEIL_ENV:
        DEMO_WEB_PORT = 10000
    register_deployment_settings_provider(lambda: {
        'nginx': {
            'inline_static_files_owner': UNPRIVILIGED_USER,
            'inline_static_files_group': UNPRIVILIGED_GROUP,
            'servers': create_nginx_server_settings(DEMO_WEB_HOST, DEMO_WEB_PORT)
        },
        'supervisor': {
            'programs': {
                'demo': {
                    'command': 'veil demo up'
                },
                'postgresql': {
                    'user': UNPRIVILIGED_USER
                }
            }
        },
        'postgresql': {
            'listen_addresses': 'localhost',
            'host': 'localhost',
            'port': 5432,
            'data_owner': UNPRIVILIGED_USER,
            'user': 'veil',
            'password': 'p@55word'
        },
        'veil': {
            'logging': {
                'level': 'DEBUG'
            },
            'http': {
                'host': DEMO_WEB_HOST,
                'port': DEMO_WEB_PORT
            },
            'website': {
                'inline_static_files_directory': NGINX_BASE_SETTINGS.nginx.inline_static_files_directory,
                'external_static_files_directory': NGINX_BASE_SETTINGS.nginx.external_static_files_directory
            },
            'demo_database': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'database': 'demo',
                'user': 'veil',
                'password': 'p@55word'
            }
        }
    })

init()