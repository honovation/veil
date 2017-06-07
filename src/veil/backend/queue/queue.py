from __future__ import unicode_literals, print_function, division
import traceback
from logging import getLogger
from datetime import timedelta, datetime

import sys
from pyres import ResQ
from redis.client import Redis
from tasktiger import TaskTiger
from veil_component import VEIL_ENV
from veil.utility.encoding import *
from veil_installer import *
from veil.utility.clock import *
from veil.model.event import *
from veil.server.process import *
from veil.frontend.cli import *
from veil.backend.queue.job import *
from .queue_client_installer import queue_client_config
from .queue_client_installer import queue_client_resource

LOGGER = getLogger(__name__)
_current_queue = None

ENQUEUE_AFTER_TIMEDELTA = timedelta(seconds=5)


def register_queue():
    add_application_sub_resource('queue_client', lambda config: queue_client_resource(**config))
    return lambda: require_queue()


def require_queue():
    global _current_queue
    if _current_queue is None:
        config = queue_client_config()
        redis = Redis(host=config.host, port=config.port)
        if 'redis' == config.type:
            _current_queue = TaskTiger(connection=redis)
        elif 'immediate' == config.type:
            _current_queue = TaskTiger(connection=redis, config={'ALWAYS_EAGER': True})
        else:
            raise Exception('unknown queue type: {}'.format(config.type))
    return _current_queue


@event(EVENT_PROCESS_TEARDOWN)
def release_queue():
    global _current_queue
    if _current_queue:
        if not VEIL_ENV.is_test:
            LOGGER.debug('close queue at exit: %(queue)s', {'queue': _current_queue})
        _current_queue = None


class RedisQueue(object):
    def __init__(self, resq):
        self.opened_by = to_unicode(b''.join(traceback.format_stack()), strict=False)
        self.resq = resq

    def enqueue(self, job_handler, to_queue=None, **payload):
        assert getattr(job_handler, 'perform'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
        for k in payload:
            if isinstance(payload[k], datetime):
                payload[k] = convert_datetime_to_utc_timezone(payload[k])
        to_queue = to_queue or job_handler.queue
        self.resq.enqueue_from_string('{}.{}'.format(job_handler.__module__, job_handler.__name__), to_queue, payload)

    def enqueue_at(self, job_handler, scheduled_at, to_queue=None, **payload):
        """
        pyres expects that scheduled_at is a naive local time
        convert_datetime_to_naive_local is to convert a datetime to naive local date time, this is an okay workaround as all servers are in UTC in production
        ideally it is to change pyres to stick with UTC and convert aware datetime to UTC in pyres interfaces such as enqueu_at
        """
        assert getattr(job_handler, 'perform'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
        scheduled_at = convert_datetime_to_utc_timezone(scheduled_at)
        for k in payload:
            if isinstance(payload[k], datetime):
                payload[k] = convert_datetime_to_utc_timezone(payload[k])
        to_queue = to_queue or job_handler.queue
        self.resq.enqueue_at_from_string(convert_datetime_to_naive_local(scheduled_at), '{}.{}'.format(job_handler.__module__, job_handler.__name__),
            to_queue, payload)

    def enqueue_after(self, job_handler, seconds_to_delay=5, **payload):
        self.enqueue_at(job_handler, get_current_time() + timedelta(seconds=seconds_to_delay), **payload)

    def enqueue_then(self, job_handler, action, seconds_to_delay=5, **payload):
        """
        if the action being executed before enqueue the job
        there is a chance that the action succeeds, but the job is not enqueued
        it is better to enqueue the job first, then do the action
        even if the job being executed before the completion of the action or the action fails
        we still have chance to retry the job from pyres web several times before we decide to pass it
        """
        self.enqueue_after(job_handler, seconds_to_delay=seconds_to_delay, **payload)
        action()

    def clear(self):
        self.resq.redis.flushall()

    def close(self):
        self.resq.close()

    def __repr__(self):
        return 'Queue {} opened by {}'.format(self.__class__, self.opened_by)


class ImmediateQueue(object):
    def __init__(self):
        self.opened_by = to_unicode(b''.join(traceback.format_stack()), strict=False)
        self.stopped = False
        self.queued_jobs = []

    def enqueue(self, job_handler, to_queue=None, **payload):
        if self.stopped:
            self.queued_jobs.append((job_handler, payload))
        else:
            self.perform_job(job_handler, payload)

    def enqueue_at(self, job_handler, scheduled_at, to_queue=None, **payload):
        self.enqueue(job_handler, **payload)

    def enqueue_after(self, job_handler, seconds_to_delay=5, **payload):
        self.enqueue(job_handler, **payload)

    def enqueue_then(self, job_handler, action, seconds_to_delay=5, **payload):
        action()
        self.enqueue(job_handler, **payload)

    def close(self):
        pass

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        jobs = self.clear_queued_jobs()
        for job_handler, payload in jobs:
            self.perform_job(job_handler, payload)

    def clear_queued_jobs(self):
        ret = self.queued_jobs
        self.queued_jobs = []
        return ret

    def clear(self):
        self.clear_queued_jobs()

    @staticmethod
    def perform_job(job_handler, payload):
        try:
            return job_handler(**payload)
        except (IgnorableInvalidJob, AssertionError):
            LOGGER.warn('Ignored ignorable invalid job: %(job_handler_name)s, %(payload)s',
                        {'job_handler_name': job_handler.__name__, 'payload': payload}, exc_info=1)
            return

    def __repr__(self):
        return 'Queue {} opened by {}'.format(self.__class__, self.opened_by)


def is_jobs_given_up(queue_redis):
    return VEIL_ENV.is_prod and VEIL_ENV.name != queue_redis.get('reserve_job')


@script('start-processing-job')
def start_processing_jobs():
    if not VEIL_ENV.is_prod:
        print('WARNING: this is only available to run under production environment.')
        return
    print('Are you sure to notify workers to start processing jobs under production environment <{}>? [YES/NO]'.format(
        VEIL_ENV.name))
    answer = sys.stdin.readline().strip()
    if 'YES' != answer:
        print('WARNING: not started')
        return
    require_queue().connection.set('reserve_job', VEIL_ENV.name)
    print ('Started')


@script('stop-processing-job')
def stop_processing_jobs():
    if not VEIL_ENV.is_prod:
        print('WARNING: this is only available to run under production environment.')
        return
    print('Are you sure to notify workers to stop processing jobs under production environment <{}>? [YES/NO]'.format(
        VEIL_ENV.name))
    answer = sys.stdin.readline().strip()
    if 'YES' != answer:
        print('WARNING: not stopped')
        return
    require_queue().connection.delete('reserve_job')
    print ('Stopped')
