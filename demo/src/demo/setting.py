from __future__ import unicode_literals, print_function, division
from veil.environment import VEIL_ENV, VEIL_HOME
from veil.frontend.web.nginx import *
from veil.backend.queue import queue_program
from veil.backend.queue import resweb_program
from veil.backend.queue import delayed_job_scheduler_program
from veil.backend.queue import job_worker_program
from veil.backend.database.postgresql import *
from veil.backend.redis import *
from veil.model.collection import *
from veil.supervisor import *
from veil.backend.queue.server import *

def demo_settings():
    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    if 'test' == VEIL_ENV:
        DEMO_WEB_PORT = 10000
    settings = objectify({
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
            }
        }
    })
    settings.update(redis_settings('demo'))
    settings.update(nginx_settings())
    settings.update(postgresql_settings('demo', user='veil', password='p@55word'))
    settings.update(pyres_settings())
    settings.update(supervisor_settings(programs={
        'demo': {'command': 'veil website demo up'},
        'postgresql': postgresql_program('demo'),
        'redis': redis_program('demo'),
        'nginx': nginx_program(),
        'queue': queue_program(),
        'resweb': resweb_program(),
        'delayed_job_scheduler': delayed_job_scheduler_program(),
        'job_worker': job_worker_program('demo')
    }))
    add_reverse_proxy_server(settings, 'veil-demo', DEMO_WEB_HOST, DEMO_WEB_PORT)
    return settings