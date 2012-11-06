from __future__ import unicode_literals, print_function, division
import veil_component
from veil.environment.setting import *
from veil.environment.installation import *
from ..job import list_job_handlers
from ..queue_api_installer import install_queue_api

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')
get_worker_interval = register_option('queue', 'worker_interval', int, default=5)


@installation_script('install-worker')
def install_worker(queue_name):
    install_queue_api()
    for job_handler in list_job_handlers(queue_name):
        component_name = veil_component.get_root_component(job_handler.__module__)
        install_dependency(component_name, install_dependencies_of_dependency=True)
