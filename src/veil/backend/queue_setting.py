from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from .redis_setting import redis_program


def queue_program(host, port):
    return objectify({'queue': redis_program('queue', host, port, persisted_by_aof=True).queue_redis})


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
            'execute_command': 'veil sleep 3 pyres_scheduler --host={} --port={} -l {} -f stderr'.format(queue_host, queue_port, logging_level),
            'priority': 210,
            'resources': [('veil_installer.component_resource', {'name': 'veil.backend.queue'})],
            'startretries': 10
        }
    })


def periodic_job_scheduler_program(application_logging_levels, application_config):
    veil_logging_level_config_path = VEIL_ETC_DIR / 'periodic-job-scheduler-log.cfg'
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=application_logging_levels),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=list_dynamic_dependency_providers('periodic-job', '@'), config=application_config)
    ]
    return objectify({
        'periodic_job_scheduler': {
            'execute_command': 'veil backend queue periodic-job-scheduler-up',
            'priority': 220,
            'environment_variables': {
                'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                'VEIL_LOGGING_EVENT': 'True'
            },
            'redirect_stderr': False,
            'resources': resources,
            'patchable': True
        }
    })


def job_worker_program(worker_name, pyres_worker_logging_level, application_logging_levels, queue_host, queue_port, queue_names, application_config,
        run_as=None, count=1, timeout=120):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-worker-log.cfg'.format(worker_name)
    application_component_names = set(name for queue_name in queue_names for name in list_dynamic_dependency_providers('job', queue_name))
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=application_logging_levels),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=application_component_names, config=application_config)
    ]
    pyrse_log_path = VEIL_LOG_DIR / '{}_worker-pyres.log'.format(worker_name)
    programs = {}
    for i in range(count):
        programs.update({
            '{}_worker{}'.format(worker_name, i + 1): {
                'execute_command': 'veil sleep 10 veil backend queue pyres_worker --host={} --port={} -t {} -l {} -f {} {}'.format(
                    queue_host, queue_port, timeout, pyres_worker_logging_level, pyrse_log_path, ','.join(queue_names)
                ), # log instruction for the main process, a.k.a pyres_worker
                'environment_variables': {
                    'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                    'VEIL_LOGGING_EVENT': 'True'
                }, # log instruction for the sub-process forked from pyres_worker, a.k.a our code
                'group': 'workers',
                'run_as': run_as or CURRENT_USER,
                'priority': 200,
                'resources': resources,
                'startretries': 10,
                'startsecs': 5,
                'redirect_stderr': False,
                'patchable': True
            }
        })
    return objectify(programs)


def job_worker_manager_program(worker_manager_name, pool_size, pyres_worker_logging_level, application_logging_levels, queue_host, queue_port, queue_names,
                               application_config, run_as=None, count=1, max_jobs=None, manager_interval=2, minion_interval=5):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-worker-log.cfg'.format(worker_manager_name)
    application_component_names = set(name for queue_name in queue_names for name in list_dynamic_dependency_providers('job', queue_name))
    resources = [
        veil_logging_level_config_resource(path=veil_logging_level_config_path, logging_levels=application_logging_levels),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=application_component_names, config=application_config)
    ]
    pyrse_log_path = VEIL_LOG_DIR / '{}_worker-manager-pyres.log'.format(worker_manager_name)
    programs = {}
    for i in range(count):
        max_jobs_term = '-j {}'.format(max_jobs) if max_jobs else ''
        programs.update({
            '{}_worker_manager{}'.format(worker_manager_name, i + 1): {
                'execute_command': 'veil sleep 10 pyres_manager --host={} --port={} --pool {} -i {} --minions_interval {} -l {} -f {} --concat_minions_logs {} {}'.format(
                    queue_host, queue_port, pool_size, manager_interval, minion_interval, pyres_worker_logging_level, pyrse_log_path, max_jobs_term, ','.join(queue_names)
                ), # log instruction for the main process, a.k.a pyres_worker
                'environment_variables': {
                    'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                    'VEIL_LOGGING_EVENT': 'True'
                }, # log instruction for the sub-process forked from pyres_worker, a.k.a our code
                'group': 'worker_manager',
                'run_as': run_as or CURRENT_USER,
                'priority': 200,
                'resources': resources,
                'startretries': 10,
                'startsecs': 5,
                'redirect_stderr': False,
                'patchable': True
            }
        })
    return objectify(programs)
