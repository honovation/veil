from __future__ import unicode_literals, print_function, division
import pyres
import pyres.scheduler
from veil.frontend.cli import *
from veil.environment.setting import *

get_queue_host = register_option('queue', 'host')
get_queue_port = register_option('queue', 'port', int)
get_queue_password = register_option('queue', 'password')


@script('delayed-job-scheduler-up')
def bring_up_delayed_job_scheduler(*argv):
    pyres.scheduler.Scheduler.run(
        pyres.ResQ('{}:{}'.format(get_queue_host(), get_queue_port()), get_queue_password()))
