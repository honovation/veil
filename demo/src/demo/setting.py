from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.web.launcher import *
from veil.frontend.web.nginx import *
from veil.backend.queue import *
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
            }
        }
    })
    settings = merge_settings(settings, redis_settings('demo'))
    settings = merge_settings(settings, nginx_settings())
    settings = merge_settings(settings, postgresql_settings('demo', user='veil', password='p@55word'))
    settings = merge_settings(settings, queue_settings())
    settings = merge_settings(settings, supervisor_settings(programs={
        'demo': website_program('demo'),
        'postgresql': postgresql_program('demo'),
        'redis': redis_program('demo'),
        'nginx': nginx_program(),
        'queue': queue_program(),
        'resweb': resweb_program(),
        'delayed_job_scheduler': delayed_job_scheduler_program(),
        'job_worker': job_worker_program('demo')
    }))
    settings = merge_settings(settings, website_settings(
        'demo', host=DEMO_WEB_HOST, port=DEMO_WEB_PORT,
        master_template_directory=VEIL_HOME / 'src' / 'demo' / 'website' / 'demo'))
    add_reverse_proxy_server(settings, 'demo')
    return settings