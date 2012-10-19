from __future__ import unicode_literals, print_function, division
import pyres
import pyres.scheduler
from veil.frontend.cli import *
from veil.environment.setting import *
from veil.environment.installation import *
from ..queue_installer import install_queue_api

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')

def delayed_job_scheduler_program():
    return  {
        'execute_command': 'veil backend queue delayed-job-scheduler-up',
        'install_command': 'veil backend queue install-delayed-job-scheduler'
    }


@script('delayed-job-scheduler-up')
def bring_up_delayed_job_scheduler(*argv):
    pyres.scheduler.Scheduler.run(
        pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password()))


@installation_script('install-delayed-job-scheduler')
def install_delayed_job_scheduler():
    install_queue_api()