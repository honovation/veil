from __future__ import unicode_literals, print_function, division
from datetime import datetime
from inspect import isfunction
from logging import getLogger
from veil_component import *
from veil.utility.clock import *

LOGGER = getLogger(__name__)


def job(queue, retry_every=None, retry_timeout=0, hard_timeout=None, unique=None, lock=None, lock_key=None, retry=None, retry_on=None, retry_method=None,
        batch=False):
    if isfunction(queue):
        job_handler = queue
        return JobHandlerDecorator(None, retry_every=retry_every, retry_timeout=retry_timeout, hard_timeout=hard_timeout, unique=unique, lock=lock,
                                   lock_key=lock_key, retry=retry, retry_on=retry_on, retry_method=retry_method, batch=batch)(job_handler)
    else:
        return JobHandlerDecorator(queue, retry_every=retry_every, retry_timeout=retry_timeout, hard_timeout=hard_timeout, unique=unique, lock=lock,
                                   lock_key=lock_key, retry=retry, retry_on=retry_on, retry_method=retry_method, batch=batch)


class JobHandlerDecorator(object):
    def __init__(self, queue, retry_every=None, retry_timeout=0, hard_timeout=None, unique=None, lock=None, lock_key=None, retry=None, retry_on=None, 
                 retry_method=None, batch=False):
        self.queue = queue
        self.retry_every = retry_every
        self.retry_timeout = retry_timeout
        self.hard_timeout = hard_timeout
        self.unique = unique
        self.lock = lock
        self.lock_key = lock_key
        self.retry = retry
        self.retry_on = retry_on
        self.retry_method = retry_method
        self.batch = batch

    def __call__(self, job_handler):
        queue = self.queue or job_handler.__name__.replace('_job', '')
        assert queue
        record_dynamic_dependency_provider(get_loading_component_name(), 'job', queue)

        if self.hard_timeout is not None:
            job_handler._task_hard_timeout = self.hard_timeout
        if queue is not None:
            job_handler._task_queue = queue
        if self.unique is not None:
            job_handler._task_unique = self.unique
        if self.lock is not None:
            job_handler._task_lock = self.lock
        if self.lock_key is not None:
            job_handler._task_lock_key = self.lock_key
        if self.retry is not None:
            job_handler._task_retry = self.retry
        if self.retry_on is not None:
            job_handler._task_retry_on = self.retry_on
        if self.retry_method is not None:
            job_handler._task_retry_method = self.retry_method
        if self.batch is not None:
            job_handler._task_batch = self.batch
        
        job_handler.retry_every = self.retry_every
        job_handler.retry_timeout = self.retry_timeout
        job_handler.perform = lambda payload: perform(job_handler, payload)
        return job_handler


def perform(job_handler, payload):
    # restore datetime as utc timezone
    for key, value in payload.items():
        if isinstance(value, datetime):
            payload[key] = convert_datetime_to_utc_timezone(value, tzinfo=pytz.utc)
    try:
        return job_handler(**payload)
    except (IgnorableInvalidJob, AssertionError):
        LOGGER.warn('Ignored ignorable invalid job: %(job_handler_name)s, %(payload)s', {'job_handler_name': job_handler.__name__, 'payload': payload},
                    exc_info=1)
        return


class IgnorableInvalidJob(Exception):
    pass
