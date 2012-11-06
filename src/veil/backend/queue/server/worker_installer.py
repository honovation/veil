from __future__ import unicode_literals, print_function, division
import veil_component
from veil_installer import installer
from veil_installer import component_resource
from ..job import list_job_handlers

@installer('queue_worker')
def install_queue_worker(dry_run_result, name):
    queue_name = name
    resources = []
    for job_handler in list_job_handlers(queue_name):
        component_name = veil_component.get_root_component(job_handler.__module__)
        resources.append(component_resource(component_name))
    return [], resources
