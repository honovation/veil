from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.setting import *
from veil.backend.shell import *

@script('up')
def bring_up_redis_server(purpose):
    settings = get_settings()
    config = getattr(settings, '{}_redis'.format(purpose))
    pass_control_to('redis-server {}'.format(config.configfile))