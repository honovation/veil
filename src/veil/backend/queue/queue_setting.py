from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.backend.redis import *

def queue_settings(resweb_host=None, resweb_port=None, workers=None, **updates):
    updates['port'] = updates.get('port', 6389)
    settings = redis_settings('queue', **updates)
    settings = merge_settings(settings, {
        'resweb': {
            'config_file': VEIL_ETC_DIR / 'resweb.cfg',
            'server_host': resweb_host or 'localhost',
            'server_port': resweb_port or 7070
        }
    })
    settings = merge_settings(settings, {
        'supervisor': {
            'programs': {
                'resweb': resweb_program(),
                'delayed_job_scheduler': delayed_job_scheduler_program(),
                'periodic_job_scheduler': periodic_job_scheduler_program()
            }
        }
    })
    workers = workers or None
    for queue_name, workers_count in workers.items():
        for i in range(1, workers_count + 1):
            settings.supervisor.programs['{}_worker{}'.format(queue_name, i)] = job_worker_program(queue_name)
    if 'test' == VEIL_ENV:
        settings.supervisor.programs.clear()
    return settings


def copy_queue_settings_to_veil(settings):
    if 'queue_redis' not in settings:
        return settings
    return merge_settings(settings, {
        'veil': {
            'queue': {
                'type': 'redis',
                'host': settings.queue_redis.bind,
                'port': settings.queue_redis.port,
                'password': settings.queue_redis.password
            } if 'test' != VEIL_ENV else {
                'type': 'immediate'
            }
        }
    }, overrides=True)


def resweb_program():
    return {
        'execute_command': 'resweb',
        'install_command': 'veil backend queue install-resweb',
        'environment_variables': {
            'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
        }
    }


def delayed_job_scheduler_program():
    return  {
        'execute_command': 'veil backend queue delayed-job-scheduler-up',
        'install_command': 'veil backend queue install-delayed-job-scheduler'
    }


def periodic_job_scheduler_program():
    return {
        'execute_command': 'veil backend queue periodic-job-scheduler-up',
        'install_command': 'veil backend queue install-periodic-job-scheduler'
    }


def job_worker_program(queue_name):
    return {
        'execute_command': 'veil backend queue worker-up {}'.format(queue_name),
        'install_command': 'veil backend queue install-worker {}'.format(queue_name)
    }
