from __future__ import unicode_literals, print_function, division
from logging import getLogger
from math import ceil
import time
import signal
import argparse
from veil.frontend.cli import *
from veil.utility.clock import *
from ..periodic_job import schedules
from ..queue import require_queue

LOGGER = getLogger(__name__)

@script('periodic-job-scheduler-up')
def bring_up_periodic_job_scheduler(*argv):
    argument_parser = argparse.ArgumentParser('Periodic job scheduler')
    argument_parser.add_argument('--dependency', type=str,
        help='where @periodic_job is defined', nargs='+', dest='dependencies')
    args = argument_parser.parse_args(argv)
    for dependency in args.dependencies:
        __import__(dependency)
    PeriodicJobScheduler().run()


class PeriodicJobScheduler(object):
    def __init__(self):
        self.stopped = False
        self.last_handle_at = None
        self.next_handle_at = None

    def register_signal_handlers(self):
        LOGGER.info('registering signals')
        signal.signal(signal.SIGTERM, self.schedule_shutdown)
        signal.signal(signal.SIGINT, self.schedule_shutdown)
        signal.signal(signal.SIGQUIT, self.schedule_shutdown)

    def schedule_shutdown(self, signal, frame):
        LOGGER.info('shutting down started')
        self.stopped = True

    def run(self):
        LOGGER.info('starting up')
        self.register_signal_handlers()
        if schedules:
            for schedule in schedules:
                jobs = ', '.join({str(job_handler) for job_handler in schedules[schedule]})
                LOGGER.info('schedule loaded: schedule is %(schedule)s and jobs are %(jobs)s', {
                    'schedule': schedule,
                    'jobs': jobs
                })
        else:
            LOGGER.error('no schedule of periodic job, exit!')
            return
        while not self.stopped:
            self.handle()
            self.wait_until_next()
        LOGGER.info('shutting down complete')

    def handle(self):
        now = get_current_timestamp()
        earliest_next = float('inf')
        for schedule in schedules:
            next = schedule.get_next_timestamp(self.last_handle_at)
            if next <= now:
                for job_handler in schedules[schedule]:
                    LOGGER.info('job due: about to enqueue %(job_handler)s', {
                        'job_handler': job_handler
                    })
                    require_queue().enqueue(job_handler)
                next = schedule.get_next_timestamp(now)
            earliest_next = min(next, earliest_next)
        self.last_handle_at = now
        self.next_handle_at = earliest_next

    def wait_until_next(self):
        now = get_current_timestamp()
        seconds = max(0, ceil(self.next_handle_at - now))
        LOGGER.debug('nothing to do: going to sleep %(seconds)s', {
            'seconds': seconds
        })
        time.sleep(seconds)
