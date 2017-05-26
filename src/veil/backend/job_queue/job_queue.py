# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import inspect
import logging
import functools

from datetime import timedelta
from tasktiger import TaskTiger
from redis import Redis
from veil.model.event import *
from veil.server.process import *
from veil.utility.json import *
from veil_component import record_dynamic_dependency_provider, get_loading_component_name, VEIL_ENV
from .queue_client_installer import queue_client_config


LOGGER = logging.getLogger(__name__)

ENQUEUE_AFTER_TIMEDELTA = timedelta(seconds=5)
DEFAULT_QUEUE_NAME = 'default'


@event(EVENT_PROCESS_TEARDOWN)
def release_queue():
    ins = JobQueue.release()
    if ins:
        if not VEIL_ENV.is_test:
            LOGGER.debug('close queue at exit: %(queue)s', {'queue': ins})


class JobQueue(TaskTiger):
    _instance = None

    @classmethod
    def release(cls):
        if cls._instance:
            ins = cls._instance
            cls._instance = None
            return ins

    @classmethod
    def instance(cls):
        if cls._instance is None:
            config = queue_client_config()
            redis = Redis(host=config.host, port=config.port)
            if 'redis' == config.type:
                cls._instance = cls(connection=redis)
            elif 'immediate' == config.type:
                cls._instance = cls(connection=redis, config={'ALWAYS_EAGER': True})
            else:
                raise Exception('unknown queue type: {}'.format(config.type))
        return cls._instance

    def delay(self, func, args=None, kwargs=None, queue=None,
              hard_timeout=None, unique=None, lock=None, lock_key=None,
              when=None, retry=None, retry_on=None, retry_method=None):
        if not self.config['ALWAYS_EAGER']:
            args_json = [to_json(a) for a in args] if args else []
            kwargs_json = {k: to_json(v) for k, v in kwargs.items()} if kwargs else {}
            _args = ({'a': args_json, 'k': kwargs_json}, )
            _kwargs = {}
        else:
            when = None  # reset for QUEUED status and execute job handler immediately
            _args = args
            _kwargs = kwargs
        return super(JobQueue, self).delay(func, args=_args, kwargs=_kwargs, queue=queue, hard_timeout=hard_timeout, unique=unique, lock=lock,
                                           lock_key=lock_key, when=when, retry=retry, retry_on=retry_on, retry_method=retry_method)


def task(queue=DEFAULT_QUEUE_NAME, hard_timeout=None, unique=None, lock=None, lock_key=None, retry=None, retry_on=None, retry_method=None, batch=False):

    job_queue = JobQueue.instance()

    def wrapper(func):
        record_dynamic_dependency_provider(get_loading_component_name(), 'job', queue)

        def _delay(f, when=None):
            @functools.wraps(f)
            def _delay_inner(*args, **kwargs):
                _queue = kwargs.pop('queue', None)
                _hard_timeout = kwargs.pop('hard_timeout', None)
                _unique = kwargs.pop('unique', None)
                _lock = kwargs.pop('lock', None)
                _lock_key = kwargs.pop('lock_key', None)
                _when = kwargs.pop('when', None) or when
                _retry = kwargs.pop('retry', None)
                _retry_on = kwargs.pop('retry_on', None)
                _retry_method = kwargs.pop('retry_method', None)
                return job_queue.delay(f, args=args, kwargs=kwargs, queue=_queue, hard_timeout=_hard_timeout, unique=_unique, lock=_lock, lock_key=_lock_key,
                                       when=_when, retry=_retry, retry_on=_retry_on, retry_method=_retry_method)
            return _delay_inner

        def _wrap(f):
            @functools.wraps(f)
            def func_wrapper(*_args, **_kwargs):
                frm = inspect.stack()[1]
                mod = inspect.getmodule(frm[0])
                if mod.__name__ == 'tasktiger.worker':
                    a = [from_json(a) for a in _args[0]['a']]
                    k = {k: from_json(v) for k, v in _args[0]['k']}
                else:
                    a = _args
                    k = _kwargs
                return f(*a, **k)

            if hard_timeout is not None:
                func_wrapper._task_hard_timeout = hard_timeout
            func_wrapper._task_queue = queue
            if unique is not None:
                func_wrapper._task_unique = unique
            if lock is not None:
                func_wrapper._task_lock = lock
            if lock_key is not None:
                func_wrapper._task_lock_key = lock_key
            if retry is not None:
                func_wrapper._task_retry = retry
            if retry_on is not None:
                func_wrapper._task_retry_on = retry_on
            if retry_method is not None:
                func_wrapper._task_retry_method = retry_method
            if batch is not None:
                func_wrapper._task_batch = batch

            func_wrapper.delay = _delay(func_wrapper)
            func_wrapper.delay_when = _delay(func_wrapper, when=ENQUEUE_AFTER_TIMEDELTA)

            return func_wrapper

        return _wrap(func)

    return wrapper


# TODO: custom Worker with start/stop processing jobs implementation
