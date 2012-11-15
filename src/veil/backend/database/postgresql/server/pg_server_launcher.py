from __future__ import unicode_literals, print_function, division
from veil.utility.shell import *
from veil.frontend.cli import *
from veil.environment.setting import *

@script('server-up')
def bring_up_postgresql_server(purpose):
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(purpose))
    pass_control_to('postgres -D {}'.format(config.data_directory))