# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import inspect
import logging
import functools
from datetime import timedelta, datetime
from croniter.croniter import croniter
from flask import Flask
from flask_admin import Admin
from tasktiger_admin import TaskTigerView, tasktiger_admin
from tasktiger import TaskTiger, JobTimeoutException, fixed, linear, exponential
from tasktiger import periodic as _periodic
from redis import Redis
from veil.frontend.cli import *
from veil.model.event import *
from veil.server.process import *
from veil.utility.clock import *
from veil.utility.json import *
from veil_component import record_dynamic_dependency_provider, get_loading_component_name, VEIL_ENV
from .queue_client_installer import queue_client_config


LOGGER = logging.getLogger(__name__)

ENQUEUE_AFTER_TIMEDELTA = timedelta(seconds=5)
DEFAULT_QUEUE_NAME = 'default'

periodic = _periodic


def _cron_expr(naive_utc_dt, expr):
    aware_utc_dt = convert_naive_datetime_to_aware(naive_utc_dt, tzinfo=pytz.utc)
    local_dt = convert_datetime_to_client_timezone(aware_utc_dt)
    next_dt = croniter(expr, start_time=local_dt).get_next(ret_type=datetime)
    return convert_datetime_to_utc_timezone(next_dt)


def cron_expr(cron_expression):
    return _cron_expr, (cron_expression, )


@event(EVENT_PROCESS_TEARDOWN)
def release_queue():
    ins = JobQueue.release()
    if ins:
        if not VEIL_ENV.is_test:
            LOGGER.debug('close queue at exit: %(queue)s', {'queue': ins})


@script('worker')
def job_queue_worker_script(modules, queues):
    JobQueue.instance().run_worker(queues=queues, module=modules)


@script('admin')
def job_queue_admin_script(listen_host, listen_port):
    app = Flask(__name__)
    app.register_blueprint(tasktiger_admin)
    admin = Admin(app, url='/')
    admin.add_view(TaskTigerView(JobQueue.instance(), name='TaskTiger', endpoint='tasktiger'))
    app.run(host=listen_host, port=int(listen_port))


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
                cls._instance = cls(connection=redis, config={'LOGGER_NAME': 'veil.backend.job_queue'})
            elif 'immediate' == config.type:
                cls._instance = cls(connection=redis, config={'ALWAYS_EAGER': True, 'LOGGER_NAME': 'veil.backend.job_queue'})
            else:
                raise Exception('unknown queue type: {}'.format(config.type))
        return cls._instance

    def delay(self, func, args=None, kwargs=None, queue=None,
              hard_timeout=None, unique=None, lock=None, lock_key=None,
              when=None, retry=None, retry_on=None, retry_method=None):
        if not self.config['ALWAYS_EAGER']:
            args_json = [to_json(a) for a in args] if args else []
            kwargs_json = {k: to_json(v) for k, v in kwargs.items()} if kwargs else {}
            _args = ({'a': args_json, 'k': kwargs_json}, ) if args_json or kwargs_json else ()
            _kwargs = {}
        else:
            when = None  # reset for QUEUED status and execute job handler immediately
            _args = args
            _kwargs = kwargs
        return super(JobQueue, self).delay(func, args=_args, kwargs=_kwargs, queue=queue, hard_timeout=hard_timeout, unique=unique, lock=lock,
                                           lock_key=lock_key, when=when, retry=retry, retry_on=retry_on, retry_method=retry_method)


def task(queue=DEFAULT_QUEUE_NAME, hard_timeout=3 * 60, unique=None, lock=None, lock_key=None, retry=True, retry_on=(JobTimeoutException, Exception),
         retry_method=exponential(60, 2, 5), schedule=None, batch=False):

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
                    a = [from_json(a) for a in _args[0]['a']] if _args else ()
                    k = {k: from_json(v) for k, v in _args[0]['k'].items()} if _args else {}
                else:
                    a = _args
                    k = _kwargs
                return f(*a, **k)

            _func_wrapper = job_queue.task(queue=queue, hard_timeout=hard_timeout, unique=unique, lock=lock, lock_key=lock_key, retry=retry, retry_on=retry_on,
                                           retry_method=retry_method, schedule=schedule, batch=batch)(func_wrapper)
            _func_wrapper.delay = _delay(_func_wrapper)
            _func_wrapper.delay_after = _delay(_func_wrapper, when=ENQUEUE_AFTER_TIMEDELTA)

            return _func_wrapper

        return _wrap(func)

    return wrapper


# TODO: custom Worker with start/stop processing jobs implementation
