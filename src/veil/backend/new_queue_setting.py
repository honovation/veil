from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.model.collection import *
from veil.environment import *
from veil.backend.new_redis_setting import redis_program


def queue_program(host, port):
    return objectify({
        'queue': redis_program('queue', host, port).queue_redis
    })


def resweb_program(resweb_host, resweb_port, queue_host, queue_port):
    return objectify({
        'resweb': {
            'execute_command': 'resweb',
            'environment_variables': {'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'},
            'installer_providers': ['veil.backend.queue'],
            'resources': [('resweb', {
                'resweb_host': resweb_host,
                'resweb_port': resweb_port,
                'queue_host': queue_host,
                'queue_port': queue_port
            })]
        }
    })


def delayed_job_scheduler_program(queue_host, queue_port):
    return objectify({
        'delayed_job_scheduler': {
            'execute_command': 'veil sleep 3 pyres_scheduler --host={} --port={} -l info -f stderr'.format(
                queue_host, queue_port),
            'installer_providers': [],
            'resources': [('python_package', {'name': 'pyres'})],
            'startretries': 10
        }
    })


def periodic_job_scheduler_program(dependencies):
    resources = [component_resource('veil.backend.queue')]
    for dependency in dependencies:
        resources.append(component_resource(dependency))
    additional_args = []
    for dependency in dependencies:
        additional_args.append('--dependency {}'.format(dependency))
    return objectify({
        'periodic_job_scheduler': {
            'execute_command': 'veil backend queue periodic-job-scheduler-up {}'.format(' '.join(additional_args)),
            'installer_providers': [],
            'resources': resources
        }
    })


def job_worker_program(worker_name, queue_host, queue_port, queue_names, dependencies, run_as=None):
    resources = [component_resource('veil.backend.queue')]
    for dependency in dependencies:
        resources.append(component_resource(dependency))
    return objectify({
        '{}_worker'.format(worker_name): {
            'execute_command': 'veil sleep 10 pyres_worker --host={} --port={} -l debug -f stderr {}'.format(
                queue_host, queue_port, ','.join(queue_names)
            ),
            'group': 'workers',
            'run_as': run_as or CURRENT_USER,
            'resources': resources,
            'startretries': 10,
            'startsecs': 10,
            'reloads_on_change': True
        }
    })