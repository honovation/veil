from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

from veil.environment.installation import *
from ..queue_api_installer import install_queue_api

def periodic_job_scheduler_program():
    return {
        'execute_command': 'veil backend queue periodic-job-scheduler-up',
        'install_command': 'veil backend queue install-periodic-job-scheduler'
    }


@installation_script('install-periodic-job-scheduler')
def install_periodic_job_scheduler():
    install_queue_api()
