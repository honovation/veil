from __future__ import unicode_literals, print_function, division
from veil.environment.layout import VEIL_ENV, VEIL_HOME
from veil.frontend.web.nginx import nginx_reverse_proxy_server
from veil.frontend.web.nginx import nginx_program
from veil.backend.queue import queue_program
from veil.backend.queue import resweb_program
from veil.backend.queue import delayed_job_scheduler_program
from veil.backend.queue import job_worker_program
from veil.backend.database import postgresql_program
from veil.backend.redis import redis_program

def demo_settings_provider(setting):
    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    UNPRIVILIGED_USER = 'dejavu'
    UNPRIVILIGED_GROUP = 'dejavu'
    if 'test' == VEIL_ENV:
        DEMO_WEB_PORT = 10000
    return {
        'supervisor': {
            'programs': {
                'demo': {'command': 'veil website demo up'},
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
            'servers': nginx_reverse_proxy_server('veil-demo', DEMO_WEB_HOST, DEMO_WEB_PORT)
        },
        'postgresql': {
            'listen_addresses': 'localhost',
            'host': 'localhost',
            'port': 5432,
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
                'master_template_directory': VEIL_HOME / 'src' / 'demo' / 'website' / 'demo',
                'reloads_module': True,
                'recalculates_static_file_hash': True,
                'clears_template_cache': True,
                'prevents_xsrf': True

            },
            'demo_database': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'database': 'demo',
                'user': 'veil',
                'password': 'p@55word'
            },
            'demo_redis': {
                'host': setting.redis.host,
                'port': setting.redis.port
            },
            'queue': {
                'type': 'redis'
            }
        }
    }