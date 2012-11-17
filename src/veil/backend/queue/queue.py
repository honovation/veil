from __future__ import unicode_literals, print_function, division
import calendar
import traceback
import pytz
from logging import getLogger
from datetime import timedelta, datetime
from redis.client import Redis
from pyres import ResQ
from veil.utility.clock import *
from veil.backend.queue_setting import get_queue_options

LOGGER = getLogger(__name__)

_current_queue = None

def require_queue():
    global _current_queue
    queue_options = get_queue_options()
    if _current_queue is None:
        if 'redis' == queue_options.type:
            redis = Redis(host=queue_options.host, port=queue_options.port, password=queue_options.password)
            resq = ResQ(server=redis)
            _current_queue = RedisQueue(resq)
        elif 'immediate' == queue_options.type:
            _current_queue = ImmediateQueue()
        else:
            raise Exception('unknown queue type: {}'.format(queue_options.type))
    return _current_queue


def release_queue():
    global _current_queue
    _current_queue.close()
    _current_queue = None


class RedisQueue(object):
    def __init__(self, resq):
        self.opened_by = str('\n').join(traceback.format_stack())
        self.resq = resq

    def enqueue(self, job_handler, to_queue=None, **payload):
        assert getattr(job_handler, 'perform'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
        for value in payload.values():
            if isinstance(value, datetime):
                assert pytz.utc == value.tzinfo, 'must provide datetime in pytz.utc timezone'
        to_queue = to_queue or job_handler.queue
        self.resq.enqueue_from_string(
            '{}.{}'.format(job_handler.__module__, job_handler.__name__),
            to_queue, payload)

    def enqueue_at(self, job_handler, scheduled_at, to_queue=None, **payload):
        """
        pyres expects that scheduled_at is a naive local time
        to_local_datetime is to convert a datetime to naive local date time, this is an okay workaround as all servers are in UTC in production
        ideally it is to change pyres to stick with UTC and convert aware datetime to UTC in pyres interfaces such as enqueu_at
        """
        assert scheduled_at.tzinfo == pytz.utc, 'must provide datetime in pytz.utc timezone'
        assert getattr(job_handler, 'perform'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
        for value in payload.values():
            if isinstance(value, datetime):
                assert pytz.utc == value.tzinfo, 'must provide datetime in pytz.utc timezone'
        to_queue = to_queue or job_handler.queue
        self.resq.enqueue_at_from_string(
            scheduled_at, '{}.{}'.format(job_handler.__module__, job_handler.__name__),
            to_queue, payload)

    def enqueue_then(self, job_handler, action, **payload):
        """
        if the action being executed before enqueue the job
        there is a chance that the action succeeds, but the job is not enqueued
        it is better to enqueue the job first, then do the action
        even if the job being executed before the completion of the action or the action fails
        we still have chance to retry the job from pyres web several times before we decide to pass it
        """
        self.enqueue_at(job_handler, get_current_time() + timedelta(seconds=5), **payload)
        action()

    def clear(self):
        self.resq.redis.flushall()

    def close(self):
        self.resq.close()

    def __repr__(self):
        return 'Queue {} opened by {}'.format(self.__class__, self.opened_by)


class ImmediateQueue(object):
    def __init__(self):
        self.opened_by = str('\n').join(traceback.format_stack())
        self.stopped = False
        self.queued_jobs = []

    def enqueue(self, job_handler, to_queue=None, **payload):
        if self.stopped:
            self.queued_jobs.append((job_handler, payload))
        else:
            job_handler.perform(payload)

    def enqueue_at(self, job_handler, scheduled_at, to_queue=None, **payload):
        self.enqueue(job_handler, **payload)

    def enqueue_then(self, job_handler, action, **payload):
        action()
        self.enqueue(job_handler, **payload)

    def close(self):
        pass

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        jobs = self.clear_queued_jobs()
        for job, payload in jobs:
            job.perform(payload)

    def clear_queued_jobs(self):
        ret = self.queued_jobs
        self.queued_jobs = []
        return ret

    def clear(self):
        self.clear_queued_jobs()

    def __repr__(self):
        return 'Queue {} opened by {}'.format(self.__class__, self.opened_by)


def convert_datetime_to_naive_local(dt):
    return datetime.fromtimestamp(convert_datetime_to_timestamp(dt))


def convert_datetime_to_timestamp(dt):
    return calendar.timegm(dt.utctimetuple())