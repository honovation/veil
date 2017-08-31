from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from .redis_setting import redis_program


def queue_program(host, port):
    return objectify({'queue': redis_program('queue', host, port, persisted_by_aof=True).queue_redis})


def tasktiger_admin_program(host, port, broker_host, broker_port, broker_db=0):
    return objectify({
        'tasktiger_admin': {
            'execute_command': 'veil backend job-queue admin {} {}'.format(host, port),
            'resources': [('veil.backend.job_queue.tasktiger_admin_resource', {
                'host': host,
                'port': port,
                'broker_host': broker_host,
                'broker_port': broker_port,
                'broker_db': broker_db
            })]
        }
    })


def tasktiger_job_worker_program(worker_name, application_logging_levels, queue_names, application_config, run_as=None):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-worker-log.cfg'.format(worker_name)
    application_component_names = set(name for queue_name in queue_names for name in list_dynamic_dependency_providers('job', queue_name))
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=application_logging_levels),
        component_resource(name='veil.backend.job_queue'),
        application_resource(component_names=application_component_names, config=application_config)
    ]
    comma_separated_modules = ','.join(application_component_names)
    comma_separated_queues = ','.join(queue_names)
    program = {
        worker_name: {
            'execute_command': 'veil backend job-queue worker {} {}'.format(comma_separated_modules, comma_separated_queues),
            'environment_variables': {
                'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                'VEIL_LOGGING_EVENT': 'True'
            }, # log instruction for the sub-process forked from pyres_worker, a.k.a our code
            'group': 'tasktiger-workers',
            'run_as': run_as or CURRENT_USER,
            'priority': 200,
            'stopsignal': 'INT',
            'stopwaitsecs': 20,
            'resources': resources,
            'redirect_stderr': False,
            'patchable': True
        }
    }
    return objectify(program)
