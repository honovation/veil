from __future__ import unicode_literals, print_function, division
import veil.component
from veil.environment.setting import *
from veil.environment.installation import *
from veil.frontend.cli import *
from veil.frontend.locale import *
from ..job import list_job_handlers
from ..queue_api_installer import install_queue_api

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')
get_worker_interval = register_option('queue', 'worker_interval', int, default=5)


def worker_program(queue_name):
    return {
        'execute_command': 'veil backend queue worker-up {}'.format(queue_name),
        'install_command': 'veil backend queue install-worker {}'.format(queue_name)
    }


@installation_script('install-worker')
def install_worker(queue_name):
    install_queue_api()
    for job_handler in list_job_handlers(queue_name):
        component_name = veil.component.get_component_of_module(job_handler.__module__)
        install_dependency(component_name)
