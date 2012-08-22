from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.backend.shell import *
from veil.environment.installation import *

__import__('demo.website')

@installation_script()
def install_demo():
    shell_execute('veil backend database postgresql server install demo')
    active_programs = [
        'demo_website', 'demo_postgresql', 'demo_redis', 'nginx', 'queue_redis',
        'resweb', 'delayed_job_scheduler', 'job_worker']
    if 'test' == VEIL_ENV:
        active_programs.remove('demo')
    shell_execute('veil supervisor install {}'.format(' '.join(active_programs)))
    shell_execute('veil backend redis server install demo')
