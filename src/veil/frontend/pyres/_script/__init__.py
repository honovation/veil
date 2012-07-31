from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import pyres
import pyres.worker
import pyres.job
import pyres.scheduler
import pyres.horde
import pyres.job
from veil.component import force_import_module
from veil.frontend.script import script
from ..scheduler import PeriodicJobScheduler
from ..job import register_job_context_manager

def patch_pyres_job_to_load_component_encapsulated_job_handler_class():
    pyres.job.Job.safe_str_to_class = staticmethod(component_aware_safe_str_to_class)


def component_aware_safe_str_to_class(qualified_class_name):
    segments = qualified_class_name.split('.')
    class_name = segments[-1]
    qualified_module_name = '.'.join(segments[:-1])
    return getattr(force_import_module(qualified_module_name), class_name)


patch_pyres_job_to_load_component_encapsulated_job_handler_class()

@script('worker-up')
def execute_bring_up_worker(*argv):
    argument_parser = ArgumentParser('Bring up pyres worker')
    argument_parser.add_argument('--host', default='localhost')
    argument_parser.add_argument('--port', type=int, default=6379)
    argument_parser.add_argument('--password')
    argument_parser.add_argument('--interval', default=5)
    argument_parser.add_argument('--context-manager', action='append')
    argument_parser.add_argument('queues', metavar='queue', type=str, nargs='+', help='where to pick job from')
    args = argument_parser.parse_args(argv)
    bring_up_worker(
        host=args.host, port=args.port, password=args.password, interval=args.interval,
        queues=args.queues, context_managers=load_context_managers(args.context_manager))


def bring_up_worker(host, port, password, interval, queues, context_managers):
    for context_manager in context_managers:
        register_job_context_manager(context_manager)
    pyres.worker.Worker.run(
        queues=queues, interval=interval,
        server=pyres.ResQ('{}:{}'.format(host, port), password))


@script('manager-up')
def execute_bring_up_manager(*argv):
    argument_parser = ArgumentParser('Bring up pyres manager')
    argument_parser.add_argument('--host', default='localhost')
    argument_parser.add_argument('--port', type=int, default=6379)
    argument_parser.add_argument('--password')
    argument_parser.add_argument('--interval', default=5)
    argument_parser.add_argument('--pool-size', default=1, type=int)
    argument_parser.add_argument('--context-manager', action='append')
    argument_parser.add_argument('queues', metavar='queue', type=str, nargs='+', help='where to pick job from')
    args = argument_parser.parse_args(argv)
    bring_up_manager(
        host=args.host, port=args.port, password=args.password, interval=args.interval,
        queues=args.queues, pool_size=args.pool_size,
        context_managers=load_context_managers(args.context_manager))


def bring_up_manager(host, port, password, interval, queues, pool_size, context_managers):
    for context_manager in context_managers:
        register_job_context_manager(context_manager)
    manager = pyres.horde.Khan(pool_size=pool_size, queues=queues, server='{}:{}'.format(host, port), password=password)
    manager.work(interval=interval)


@script('delayed-job-scheduler-up')
def execute_bring_up_delayed_job_scheduler(*argv):
    argument_parser = ArgumentParser('Bring up delayed job scheduler')
    argument_parser.add_argument('--host', default='localhost')
    argument_parser.add_argument('--port', type=int, default=6379)
    argument_parser.add_argument('--password')
    args = argument_parser.parse_args(argv)
    bring_up_delayed_job_scheduler(host=args.host, port=args.port, password=args.password)


def bring_up_delayed_job_scheduler(host, port, password):
    pyres.scheduler.Scheduler.run(pyres.ResQ('{}:{}'.format(host, port), password))


@script('periodic-job-scheduler-up')
def execute_bring_up_periodic_job_scheduler(*argv):
    argument_parser = ArgumentParser('Bring up periodic job scheduler')
    argument_parser.add_argument('--host', default='localhost')
    argument_parser.add_argument('--port', type=int, default=6379)
    argument_parser.add_argument('--password')
    argument_parser.add_argument('modules', metavar='module', type=str, nargs='+', help='where defined @periodic_job')
    args = argument_parser.parse_args(argv)
    bring_up_periodic_job_scheduler(host=args.host, port=args.port, password=args.password, modules=args.modules)


def bring_up_periodic_job_scheduler(host, port, password, modules):
    for module in modules:
        __import__(module)
    PeriodicJobScheduler(pyres.ResQ('{}:{}'.format(host, port), password)).run()


def load_context_managers(context_manager_names):
    return [component_aware_safe_str_to_class(cmn) for cmn in context_manager_names]