from __future__ import unicode_literals, print_function, division
import logging
from veil.frontend.cli import *
from veil.utility.timer import *
from .env_backup import create_env_backup

LOGGER = logging.getLogger(__name__)


@script('guard-up')
def bring_up_guard(crontab_expression):
    @run_every(crontab_expression)
    def work():
        create_env_backup()

    work()
