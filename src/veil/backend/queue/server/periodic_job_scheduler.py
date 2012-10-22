from __future__ import unicode_literals, print_function, division
from logging import getLogger
from math import ceil
import time
import signal
import pyres
from veil.frontend.cli import *
from veil.utility.clock import get_current_timestamp
from veil.environment.setting import *
from veil.environment.installation import *
from ..periodic_job import schedules
from ..job import enqueue
from ..queue_api_installer import install_queue_api

LOGGER = getLogger(__name__)

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')

def periodic_job_scheduler_program():
    return {
        'execute_command': 'veil backend queue periodic-job-scheduler-up',
        'install_command': 'veil backend queue install-periodic-job-scheduler'
    }


@installation_script('install-periodic-job-scheduler')
def install_periodic_job_scheduler():
    install_queue_api()


@script('periodic-job-scheduler-up')
def bring_up_periodic_job_scheduler(*argv):
    PeriodicJobScheduler(
        pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password())).run()


class PeriodicJobScheduler(object):
    def __init__(self, resq):
        self.resq = resq
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
                LOGGER.info('schedule for {}: {}'.format(jobs, schedule))
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
                    LOGGER.info('enqueue job {}'.format(job_handler))
                    enqueue(self.resq, job_handler)
                next = schedule.get_next_timestamp(now)
            earliest_next = min(next, earliest_next)
        self.last_handle_at = now
        self.next_handle_at = earliest_next

    def wait_until_next(self):
        now = get_current_timestamp()
        seconds = max(0, ceil(self.next_handle_at - now))
        LOGGER.debug('sleep {} seconds'.format(seconds))
        time.sleep(seconds)
