from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *
from ..queue_api_installer import install_queue_api

def delayed_job_scheduler_program():
    return  {
        'execute_command': 'veil backend queue delayed-job-scheduler-up',
        'install_command': 'veil backend queue install-delayed-job-scheduler'
    }


@installation_script('install-delayed-job-scheduler')
def install_delayed_job_scheduler():
    install_queue_api()