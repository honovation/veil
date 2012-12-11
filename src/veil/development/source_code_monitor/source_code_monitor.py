from __future__ import unicode_literals, print_function, division
import logging
import functools
import time
import threading
import discipline_coach
import os
from veil.environment import *

LOGGER = logging.getLogger(__name__)


def source_code_monitored(func):
    @functools.wraps(func)
    def wrapper(**kwargs):
        components = kwargs.pop('components')
        if 'development' == VEIL_ENV:
            if load_components(components):
                SourceCodeMonitor().start()
                return func(**kwargs)
            else:
                time.sleep(3)
                os._exit(1)
        else:
            assert load_components(components)
            return func(**kwargs)

    return wrapper


class SourceCodeMonitor(threading.Thread):
    def __init__(self):
        super(SourceCodeMonitor, self).__init__()
        self.daemon = True
        self.init_hash = discipline_coach.calculate_git_status_hash()

    def run(self):
        while True:
            try:
                time.sleep(0.5)
                current_hash = discipline_coach.calculate_git_status_hash()
                if current_hash != self.init_hash:
                    LOGGER.info('detected file change')
                    os._exit(1)
            except:
                LOGGER.exception('source code monitor died')


def load_components(components):
    before = time.time()
    for component in components:
        try:
            __import__(component)
        except:
            LOGGER.exception('failed to load component: %(component)s', {
                'component': component
            })
            return False
    after = time.time()
    LOGGER.info('all components loaded: took %(elapsed_seconds)s seconds', {
        'elapsed_seconds': after - before
    })
    return True