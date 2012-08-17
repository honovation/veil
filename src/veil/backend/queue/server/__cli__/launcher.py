from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import pyres
import pyres.worker
import pyres.job
import pyres.scheduler
from veil.component import *
from veil.environment.setting import *
from veil.frontend.cli import *
from veil.frontend.locale import *
from ..scheduler import PeriodicJobScheduler
from ..job import register_job_context_manager

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')
get_worker_interval = register_option('queue', 'worker_interval', int, default=5)

def patch_pyres_job_to_load_component_encapsulated_job_handler_class():
    pyres.job.Job.safe_str_to_class = staticmethod(component_aware_safe_str_to_class)


def component_aware_safe_str_to_class(qualified_class_name):
    segments = qualified_class_name.split('.')
    class_name = segments[-1]
    qualified_module_name = '.'.join(segments[:-1])
    return getattr(force_import_module(qualified_module_name), class_name)


patch_pyres_job_to_load_component_encapsulated_job_handler_class()

@script('worker-up')
def bring_up_worker(*argv):
    argument_parser = ArgumentParser('Bring up pyres worker')
    argument_parser.add_argument('queues', metavar='queue', type=str, nargs='+', help='where to pick job from')
    args = argument_parser.parse_args(argv)
    register_job_context_manager(require_current_locale_being_default)
    pyres.worker.Worker.run(
        queues=args.queues, interval=get_worker_interval(),
        server=pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password()))

@script('delayed-job-scheduler-up')
def ebring_up_delayed_job_scheduler(*argv):
    pyres.scheduler.Scheduler.run(
        pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password()))


@script('periodic-job-scheduler-up')
def bring_up_periodic_job_scheduler(*argv):
    PeriodicJobScheduler(
        pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password())).run()

