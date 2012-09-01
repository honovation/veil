from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.environment.setting import *
from veil.frontend.cli import script


@script('up')
def bring_up_supervisor():
    settings = get_settings()
    pass_control_to('supervisord -c {}'.format(settings.supervisor.config_file))


