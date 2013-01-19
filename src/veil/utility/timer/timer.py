from __future__ import unicode_literals, print_function, division
import functools
import logging
from veil.utility.clock import get_current_timestamp
from croniter.croniter import croniter
import time

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
                next = croniter(self.crontab_expression, now).get_next()
                delta = next - now
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