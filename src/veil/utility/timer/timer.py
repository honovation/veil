from __future__ import unicode_literals, print_function, division
import functools
import logging
from datetime import datetime
import time
from croniter.croniter import croniter
from veil.utility.clock import *

LOGGER = logging.getLogger(__name__)


def run_every(crontab_expression):
    return Timer(crontab_expression)


class Timer(object):
    def __init__(self, crontab_expression):
        self.crontab_expression = crontab_expression

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            LOGGER.info('timer started: for %(func)s to run every %(crontab_expression)s', {
                'func': func,
                'crontab_expression': self.crontab_expression
            })
            while True:
                now = get_current_timestamp()
                #TODO: remove croniter hack when croniter is fixed
                ct = croniter(self.crontab_expression, now + DEFAULT_CLIENT_TIMEZONE.utcoffset(datetime.now()).total_seconds())
                next_run = ct.get_next(ret_type=float) - DEFAULT_CLIENT_TIMEZONE.utcoffset(datetime.now()).total_seconds()
                delta = next_run - now
                LOGGER.info('timer sleep: wake up after %(delta)s seconds', {
                    'delta': delta
                })
                time.sleep(delta)
                LOGGER.info('timer woke up')
                before = time.time()
                try:
                    func(*args, **kwargs)
                finally:
                    after = time.time()
                    LOGGER.info('timer work done: in %(elapsed_time)s seconds', {
                        'elapsed_time': after - before
                    })
        return wrapper


def log_elapsed_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_seconds = time.time() - start
            LOGGER.info('Elapsed time for function execution: %(function_name)s took %(elapsed_seconds)s seconds to finish', {
                'function_name': func.__name__, 'elapsed_seconds': elapsed_seconds
            })
    return wrapper