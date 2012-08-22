from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.backend.redis import *

def queue_settings(config_file=None, server_host=None, server_port=None, **updates):
    updates['port'] = updates.get('port', 6380)
    settings = redis_settings('queue', **updates)
    settings = merge_settings(settings, {
        'resweb': {
            'config_file': config_file or VEIL_ETC_DIR / 'resweb.cfg',
            'server_host': server_host or 'localhost',
            'server_port': server_port or 7070
        }
    })
    settings = merge_settings(settings, {
        'supervisor': {
            'programs': {
                'resweb': resweb_program(),
                'delayed_job_scheduler': delayed_job_scheduler_program()
            }
        }
    })
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
            }
        }
    }, overrides=True)


def resweb_program():
    return {
        'command': 'resweb',
        'environment_variables': {
            'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
        }
    }


def delayed_job_scheduler_program():
    return  {
        'command': 'veil backend queue server delayed-job-scheduler-up'
    }


def periodic_job_scheduler_program():
    return {
        'command': 'veil backend queue server periodic-job-scheduler-up'
    }


def job_worker_program(*queues):
    return {
        'command': 'veil backend queue server worker-up {}'.format(' '.join(queues))
    }
