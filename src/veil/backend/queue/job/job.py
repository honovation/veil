from __future__ import unicode_literals, print_function, division
from datetime import datetime
from inspect import isfunction
from logging import getLogger
from veil_component import *
from veil.utility.clock import *

LOGGER = getLogger(__name__)


def job(queue, retry_every=None, retry_timeout=0):
    if isfunction(queue):
        job_handler = queue
        return JobHandlerDecorator(None, retry_every, retry_timeout)(job_handler)
    else:
        return JobHandlerDecorator(queue, retry_every, retry_timeout)


class JobHandlerDecorator(object):
    def __init__(self, queue, retry_every=None, retry_timeout=0):
        self.queue = queue
        self.retry_every = retry_every
        self.retry_timeout = retry_timeout

    def __call__(self, job_handler):
        queue = self.queue or job_handler.__name__.replace('_job', '')
        assert queue
        record_dynamic_dependency_provider(get_loading_component_name(), 'job', queue)
        job_handler.queue = queue
        job_handler.retry_every = self.retry_every
        job_handler.retry_timeout = self.retry_timeout
        job_handler.perform = lambda payload: perform(job_handler, payload)
        return job_handler


def perform(job_handler, payload):
    # restore datetime as utc timezone
    for key, value in payload.items():
        if isinstance(value, datetime):
            payload[key] = convert_datetime_to_utc_timezone(value)
    try:
        return job_handler(**payload)
    except (IgnorableInvalidJob, AssertionError):
        LOGGER.warn('Ignored ignorable invalid job: %(job_handler_name)s, %(payload)s', {'job_handler_name': job_handler.__name__, 'payload': payload},
                    exc_info=1)
        return


class IgnorableInvalidJob(Exception):
    pass
