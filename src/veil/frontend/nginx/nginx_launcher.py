from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.utility.shell import *
from veil.environment.setting import *

@script('up')
def bring_up_nginx():
    settings = get_settings()
    pass_control_to('nginx -c {}'.format(settings.nginx.config_file))
