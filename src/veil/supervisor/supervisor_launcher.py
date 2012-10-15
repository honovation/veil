from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.environment.setting import *
from veil.frontend.cli import script
from .supervisor_setting import supervisor_settings

@script('up')
def bring_up_supervisor():
    settings = get_settings()
    config = settings.supervisor if 'supervisor' in settings else supervisor_settings().supervisor
    pass_control_to('supervisord -c {}'.format(config.config_file))


