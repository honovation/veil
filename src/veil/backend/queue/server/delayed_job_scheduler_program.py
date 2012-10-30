from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

def delayed_job_scheduler_program(queue_redis_host, queue_redis_port):
    return  {
        'execute_command': 'veil execute python -m pyres_patch.pyres_scheduler --host={} --port={} -l info -f stderr'.format(
            queue_redis_host, queue_redis_port),
        'install_command': 'veil backend queue install'
    }
