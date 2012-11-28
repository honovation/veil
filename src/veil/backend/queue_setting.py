from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.model.collection import *
from veil.environment import *
from veil.backend.redis_setting import redis_program


def queue_program(host, port):
    return objectify({
        'queue': redis_program('queue', host, port).queue_redis
    })


def resweb_program(resweb_host, resweb_port, queue_host, queue_port):
    return objectify({
        'resweb': {
            'execute_command': 'resweb',
            'environment_variables': {'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'},
            'resources': [('veil.backend.queue.resweb_resource', {
                'resweb_host': resweb_host,
                'resweb_port': resweb_port,
                'queue_host': queue_host,
                'queue_port': queue_port
            })]
        }
    })


def delayed_job_scheduler_program(queue_host, queue_port, logging_level):
    return objectify({
        'delayed_job_scheduler': {
            'execute_command': 'veil sleep 3 pyres_scheduler --host={} --port={} -l {} -f stderr'.format(
                queue_host, queue_port, logging_level),
            'resources': [('veil_installer.component_resource', {'name': 'veil.backend.queue'})],
            'startretries': 10
        }
    })


def periodic_job_scheduler_program(loggers, dependencies):
    veil_log_config_path = VEIL_ETC_DIR / 'periodic-job-scheduler-log.cfg'
    resources = [
        component_resource(name='veil.backend.queue'),
        veil_log_config_resource(path=veil_log_config_path, loggers=loggers)]
    for dependency in dependencies:
        resources.append(component_resource(name=dependency))
    additional_args = []
    for dependency in dependencies:
        additional_args.append('--dependency {}'.format(dependency))
    return objectify({
        'periodic_job_scheduler': {
            'execute_command': 'veil backend queue periodic-job-scheduler-up {}'.format(' '.join(additional_args)),
            'environment_variables': {
                'VEIL_LOG': veil_log_config_path
            },
            'resources': resources
        }
    })


def job_worker_program(
        worker_name, pyres_worker_logging_level, loggers, queue_host, queue_port, queue_names,
        application_component_names, application_config, run_as=None):
    veil_log_config_path = VEIL_ETC_DIR / '{}-worker-log.cfg'.format(worker_name)
    resources = [
        veil_log_config_resource(path=veil_log_config_path, loggers=loggers),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=application_component_names, config=application_config)]
    return objectify({
        '{}_worker'.format(worker_name): {
            'execute_command': 'veil sleep 10 pyres_worker --host={} --port={} -l {} -f stderr {}'.format(
                queue_host, queue_port, pyres_worker_logging_level, ','.join(queue_names)
            ), # log instruction for the main process, a.k.a pyres_worker
            'environment_variables': {
                'VEIL_LOG': veil_log_config_path
            }, # log instruction for the sub-process forked from pyres_worker, a.k.a our code
            'group': 'workers',
            'run_as': run_as or CURRENT_USER,
            'resources': resources,
            'startretries': 10,
            'startsecs': 10,
            'reloads_on_change': application_component_names
        }
    })