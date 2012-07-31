from __future__ import unicode_literals, print_function, division
from inspect import isfunction
import contextlib
from logging import getLogger

LOGGER = getLogger(__name__)
context_managers = []

def register_job_context_manager(context_manager):
    LOGGER.info('register job context manager: {}'.format(context_manager))
    context_managers.append(context_manager)


def enqueue(resq, job_handler, **payload):
    assert getattr(job_handler, 'queue'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
    resq.enqueue(job_handler, payload)


def enqueue_at(resq, job_handler, scheduled_at, **payload):
    assert getattr(job_handler, 'queue'), 'must decorate job handler {} with @job to enqueue'.format(job_handler)
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
        job_handler.queue = self.queue or job_handler.__name__
        job_handler.perform = lambda payload: perform(job_handler, payload)
        return job_handler


def perform(job_handler, payload):
    with nest_context_managers(*context_managers):
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