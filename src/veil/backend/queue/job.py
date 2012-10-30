from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

from datetime import datetime
from inspect import isfunction
import contextlib
from logging import getLogger
from pprint import pprint
from veil.frontend.cli import *

LOGGER = getLogger(__name__)
context_managers = []
queues = {} # queue_name => job_handlers


@script('list-queues')
def list_queues():
    pprint(queues)


def register_job_context_manager(context_manager):
    LOGGER.info('register job context manager: {}'.format(context_manager))
    context_managers.append(context_manager)


def enqueue(resq, job_handler, **payload):
    import pytz

    assert getattr(job_handler, 'queue'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
    for value in payload.values():
        if isinstance(value, datetime):
            assert pytz.utc == value.tzinfo, 'must provide datetime in pytz.utc timezone'
    resq.enqueue(job_handler, payload)


def enqueue_at(resq, job_handler, scheduled_at, **payload):
    import pytz

    assert getattr(job_handler, 'queue'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
    for value in payload.values():
        if isinstance(value, datetime):
            assert pytz.utc == value.tzinfo, 'must provide datetime in pytz.utc timezone'
    resq.enqueue_at(scheduled_at, job_handler, payload)


def job(queue):
    if isfunction(queue):
        job_handler = queue
        return JobHandlerDecorator(None)(job_handler)
    else:
        return JobHandlerDecorator(queue)


class JobHandlerDecorator(object):
    def __init__(self, queue):
        self.queue = queue

    def __call__(self, job_handler):
        job_handler.queue = self.queue or job_handler.__name__.replace('_job', '')
        job_handler.perform = lambda payload: perform(job_handler, payload)
        queues.setdefault(job_handler.queue, []).append(job_handler)
        return job_handler


def perform(job_handler, payload):
    import pytz

    with nest_context_managers(*context_managers):
        # restore datetime as utc timezone
        for key, value in payload.items():
            if isinstance(value, datetime):
                payload[key] = value.replace(tzinfo=pytz.utc)
        return job_handler(**payload)


def list_job_handlers(queue_name):
    return queues.get(queue_name, [])


def nest_context_managers(*context_managers):
    context_managers = [as_context_manager(obj) for obj in context_managers]
    return contextlib.nested(*context_managers)


def as_context_manager(obj):
    if isfunction(obj):
        return obj()
    if hasattr(obj, '__enter__') and hasattr(obj, '__exit__'):
        return obj
    raise Exception('{} is not context manager'.format(obj))