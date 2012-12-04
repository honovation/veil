from __future__ import unicode_literals, print_function, division
import fabric.api
import os
import logging
import time
from croniter.croniter import croniter
from veil.frontend.cli import *
from veil.utility.clock import get_current_timestamp
from .env_backup import create_env_backup

LOGGER = logging.getLogger(__name__)

@script('guard-up')
def bring_up_guard(crontab_expression):
    while True:
        now = get_current_timestamp()
        next = croniter(crontab_expression, now).get_next()
        delta = next - now
        LOGGER.info('backup later: wake up in %(delta)s seconds', {
            'delta': delta
        })
        time.sleep(delta)
        create_env_backup()