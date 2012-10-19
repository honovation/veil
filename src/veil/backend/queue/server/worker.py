from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import pyres
import pyres.worker
from veil.environment.setting import *
from veil.frontend.cli import *
from veil.frontend.locale import *
from ..job import register_job_context_manager
from ..queue_installer import install_queue_api

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')
get_worker_interval = register_option('queue', 'worker_interval', int, default=5)

def worker_program(queue_name):
    return {
        'execute_command': 'veil backend queue worker-up {}'.format(queue_name),
        'install_command': 'veil backend queue install-worker {}'.format(queue_name)
    }


@script('worker-up')
def bring_up_worker(*argv):
    argument_parser = ArgumentParser('Bring up pyres worker')
    argument_parser.add_argument('queues', metavar='queue', type=str, nargs='+', help='where to pick job from')
    args = argument_parser.parse_args(argv)
    register_job_context_manager(require_current_locale_being_default)
    pyres.worker.Worker.run(
        queues=args.queues, interval=get_worker_interval(),
        server=pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password()))


@script('install-worker')
def install_worker(queue_name):
    install_queue_api()
    # TODO: install the components where job handlers resides in