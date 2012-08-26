from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.web.launcher import *
from veil.frontend.web.nginx import *
from veil.backend.database.postgresql import *
from veil.backend.redis import *
from veil.model.collection import *
from veil.supervisor import *
from veil.backend.queue.server import *

def demo_settings():
    settings = objectify({
        'veil': {
            'logging': {
                'level': 'DEBUG'
            }
        }
    })
    settings = merge_settings(settings, redis_settings('demo'))
    settings = merge_settings(settings, nginx_settings())
    settings = merge_settings(settings, postgresql_settings(
        'demo', user='veil', password='p@55word', owner_password='p@55word'))
    settings = merge_settings(settings, queue_settings(workers={'demo': 1}))
    settings = merge_settings(settings, website_settings(
        'demo', port=5010,
        master_template_directory=VEIL_HOME / 'src' / 'demo' / 'website' / 'demo'))
    add_reverse_proxy_server(settings, 'demo')
    settings = merge_settings(settings, supervisor_settings())
    return settings