# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import importlib
import inspect
import logging
import functools
from datetime import timedelta, datetime

import sys
from croniter.croniter import croniter
from flask import Flask
from flask_admin import Admin
from tasktiger_admin import TaskTigerView, tasktiger_admin
from tasktiger import TaskTiger, JobTimeoutException, fixed, linear, exponential
from tasktiger import periodic as _periodic
from tasktiger.redis_scripts import RedisScripts
from tasktiger.worker import Worker
from tasktiger._internal import ERROR as ERROR_QUEUE_KEY
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
ALWAYS_RETRY_ON = (JobTimeoutException, )

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


class LoadedRedisScripts(RedisScripts):
    def execute_pipeline(self, pipeline, client=None):
        if pipeline.scripts:
            pipeline.load_scripts()
        return super(LoadedRedisScripts, self).execute_pipeline(pipeline, client=client)


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
            redis = Redis(host=config.host, port=config.port, decode_responses=True)
            if 'redis' == config.type:
                cls._instance = cls(connection=redis, config={'LOGGER_NAME': 'veil.backend.job_queue', 'STATS_INTERVAL': 0, 'REQUEUE_EXPIRED_TASKS_BATCH_SIZE': 1000})
            elif 'immediate' == config.type:
                cls._instance = cls(connection=redis, config={'ALWAYS_EAGER': True, 'LOGGER_NAME': 'veil.backend.job_queue', 'STATS_INTERVAL': 0})
            else:
                raise Exception('unknown queue type: {}'.format(config.type))
            # reset tasktiger scripts
            cls._instance.scripts = LoadedRedisScripts(redis)
        return cls._instance

    def delay(self, func, args=None, kwargs=None, queue=None,
              hard_timeout=None, unique=None, lock=None, lock_key=None,
              when=None, retry=None, retry_on=None, retry_method=None):
        if self.config['ALWAYS_EAGER']:
            when = None
        args_json = [to_json(a) for a in args] if args else []
        kwargs_json = {k: to_json(v) for k, v in kwargs.items()} if kwargs else {}
        _args = ({'a': args_json, 'k': kwargs_json}, ) if args_json or kwargs_json else ()
        _kwargs = {}
        return super(JobQueue, self).delay(func, args=_args, kwargs=_kwargs, queue=queue, hard_timeout=hard_timeout, unique=unique, lock=lock,
                                           lock_key=lock_key, when=when, retry=retry, retry_on=retry_on, retry_method=retry_method)

    def run_worker(self, queues=None, module=None, exclude_queues=None):
        """
        behavior same as parent class `run_worker`, except a modified Worker class

        @param queues: queue names to listen, separated by comma
        @param module: python modules to load, separated by comma
        @param exclude_queues: format same as queues
        @return: None
        """

        module_names = module or ''
        for module_name in module_names.split(','):
            module_name = module_name.strip()
            if module_name:
                importlib.import_module(module_name)
                self.log.debug('imported module', module_name=module_name)

        worker = ControllableWorker(self,
                                    queues.split(',') if queues else None,
                                    exclude_queues.split(',') if exclude_queues else None)
        worker.run()


class ControllableWorker(Worker):
    def _worker_run(self):
        if is_jobs_given_up(self.connection):
            return
        super(ControllableWorker, self)._worker_run()


def task(queue=DEFAULT_QUEUE_NAME, hard_timeout=3 * 60, unique=True, lock=None, lock_key=None, retry=True, retry_on=(Exception, ),
         retry_method=exponential(60, 2, 5), schedule=None, batch=False):
    retry_on = retry_on + ALWAYS_RETRY_ON

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
                if mod.__name__ == 'tasktiger.worker' or job_queue.config['ALWAYS_EAGER']:
                    # ALWAYS_EAGER means sync and async call, tasktiger.worker means async call
                    if _args and isinstance(_args[0], dict) and 'a' in _args[0] and 'k' in _args[0]:
                        a = [from_json(a) for a in _args[0]['a']]
                        k = {k: from_json(v) for k, v in _args[0]['k'].items()}
                    else:
                        a = _args
                        k = _kwargs
                    expired_at = k.pop('expired_at', None)
                    current_time = get_current_time()
                    if expired_at and expired_at <= current_time:
                        LOGGER.debug('ignore expired task: %(expired_at)s, %(current)s', {'expired_at': expired_at, 'current': current_time})
                        return
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


def is_jobs_given_up(queue_redis):
    return VEIL_ENV.is_prod and VEIL_ENV.name != queue_redis.get('reserve_job')


@script('start-processing-job')
def start_processing_jobs():
    if not VEIL_ENV.is_prod:
        print('WARNING: this is only available to run under production environment.')
        return
    print('Are you sure to notify workers to start processing jobs under production environment <{}>? [YES/NO]'.format(VEIL_ENV.name))
    answer = sys.stdin.readline().strip()
    if 'YES' != answer:
        print('WARNING: not started')
        return
    JobQueue.instance().connection.set('reserve_job', VEIL_ENV.name)
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
    JobQueue.instance().connection.delete('reserve_job')
    print ('Stopped')


def count_failed_jobs():
    job_queue = JobQueue.instance()
    queue_redis = job_queue.connection
    error_queue_names = queue_redis.smembers(job_queue._key(ERROR_QUEUE_KEY))
    failed_jobs_count = 0
    for queue_name in error_queue_names:
        failed_jobs_count += queue_redis.zcard(job_queue._key(ERROR_QUEUE_KEY, queue_name))
    return failed_jobs_count
