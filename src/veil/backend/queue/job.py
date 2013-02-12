from __future__ import unicode_literals, print_function, division
from datetime import datetime
from inspect import isfunction
import contextlib
from logging import getLogger
from veil.utility.clock import convert_datetime_to_utc_timezone

LOGGER = getLogger(__name__)
context_managers = []


def register_job_context_manager(context_manager):
    context_managers.append(context_manager)
    LOGGER.info('registered job context manager: %(context_manager)s', {
        'context_manager': context_manager
    })


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
        job_handler.queue = self.queue or job_handler.__name__.replace('_job', '')
        job_handler.retry_every = self.retry_every
        job_handler.retry_timeout = self.retry_timeout
        job_handler.perform = lambda payload: perform(job_handler, payload)
        return job_handler


def perform(job_handler, payload):
    with nest_context_managers(*context_managers):
        # restore datetime as utc timezone
        for key, value in payload.items():
            if isinstance(value, datetime):
                payload[key] = convert_datetime_to_utc_timezone(value)
        return job_handler(**payload)


def nest_context_managers(*context_managers):
    context_managers = [as_context_manager(obj) for obj in context_managers]
    return contextlib.nested(*context_managers)


def as_context_manager(obj):
    if isfunction(obj):
        return obj()
    if hasattr(obj, '__enter__') and hasattr(obj, '__exit__'):
        return obj
    raise Exception('{} is not context manager'.format(obj))