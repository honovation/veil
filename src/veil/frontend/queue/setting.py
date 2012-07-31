from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *
from veil.backend.redis import *

DEFAULT_QUEUE_HOST = '127.0.0.1'
DEFAULT_QUEUE_PORT = 6380

PYRES_BASE_SETTINGS = {
    'queue': {
        'dbdir': VEIL_VAR_DIR / 'queue',
        'configfile': VEIL_ETC_DIR / 'queue.conf',
        'bind': DEFAULT_QUEUE_HOST,
        'port': DEFAULT_QUEUE_PORT,
        'password': ''
    },
    'resweb': {
        'config_file': VEIL_ETC_DIR / 'resweb.cfg',
        'server_host': 'localhost',
        'server_port': 5000
    }
}

def queue_program():
    return redis_program('queue')


def resweb_program():
    return {
        'command': 'resweb',
        'environment_variables': {
            'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
        }
    }


def delayed_job_scheduler_program():
    return  {
        'command': 'veil frontend queue delayed-job-scheduler-up'
    }


def periodic_job_scheduler_program():
    return {
        'command': 'veil frontend queue periodic-job-scheduler-up'
    }


def job_worker_program(*queues):
    return {
        'command': 'veil frontend queue worker-up {}'.format(' '.join(queues))
    }
