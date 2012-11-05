from __future__ import unicode_literals, print_function, division


def delayed_job_scheduler_program(queue_redis_host, queue_redis_port):
    return  {
        'execute_command': 'pyres_scheduler --host={} --port={} -l info -f stderr'.format(
            queue_redis_host, queue_redis_port),
        'install_command': 'veil install python_package?pyres'
    }
