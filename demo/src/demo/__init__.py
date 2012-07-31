def init():
    from veil.component import init_component
    from veil.environment.layout import VEIL_ENV, VEIL_HOME
    from veil.environment.deployment import register_deployment_settings_provider
    from veil.frontend.web.nginx import nginx_reverse_proxy_server
    from veil.frontend.web.nginx import nginx_program
    from veil.frontend.queue import queue_program
    from veil.frontend.queue import resweb_program
    from veil.frontend.queue import delayed_job_scheduler_program
    from veil.frontend.queue import job_worker_program
    from veil.backend.rdbms import postgresql_program
    from veil.backend.redis import redis_program

    init_component(__name__)

    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    UNPRIVILIGED_USER = 'dejavu'
    UNPRIVILIGED_GROUP = 'dejavu'
    if 'test' == VEIL_ENV:
        DEMO_WEB_PORT = 10000
    register_deployment_settings_provider(lambda settings: {
        'supervisor': {
            'programs': {
                'demo': {'command': 'veil demo up'},
                'postgresql': postgresql_program({'user': UNPRIVILIGED_USER}),
                'redis': redis_program(),
                'nginx': nginx_program(),
                'queue': queue_program(),
                'resweb': resweb_program(),
                'delayed_job_scheduler': delayed_job_scheduler_program(),
                'job_worker': job_worker_program('demo')
            }
        },
        'nginx': {
            'inline_static_files_owner': UNPRIVILIGED_USER,
            'inline_static_files_group': UNPRIVILIGED_GROUP,
            'servers': nginx_reverse_proxy_server(DEMO_WEB_HOST, DEMO_WEB_PORT)
        },
        'postgresql': {
            'listen_addresses': 'localhost',
            'host': 'localhost',
            'port': 5432,
            'data_owner': UNPRIVILIGED_USER,
            'user': 'veil',
            'password': 'p@55word'
        },
        'redis': {
            'owner': UNPRIVILIGED_USER
        },
        'queue': {
            'owner': UNPRIVILIGED_USER
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
                'master_template_directory': VEIL_HOME / 'src' / 'demo'
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