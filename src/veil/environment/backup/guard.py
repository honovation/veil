from __future__ import unicode_literals, print_function, division
import logging
import datetime
from veil.frontend.cli import *
from veil.model.event import *
from veil.server.process import *
from veil.utility.shell import *
from veil.utility.timer import *
from .env_backup import create_env_backup

LOGGER = logging.getLogger(__name__)

@script('guard-up')
def bring_up_guard(crontab_expression):
    @run_every(crontab_expression)
    def work():
        create_env_backup()

    work()


@event(EVENT_PROCESS_TEARDOWN)
def on_process_teardown():
    shell_execute('touch ~/has_shutdown_at_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
