from __future__ import unicode_literals, print_function, division
import logging
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *


LOGGER = logging.getLogger(__name__)

@script('up')
def bring_up_log_rotater(config_file, crontab_expression):
    @run_every(crontab_expression)
    def work():
        shell_execute('logrotate {}'.format(config_file))

    work()