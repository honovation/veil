from __future__ import unicode_literals, print_function, division
from veil.environment.layout import *

DEFAULT_QUEUE_HOST = 'localhost'
DEFAULT_QUEUE_PORT = 6380

PYRES_BASE_SETTINGS = {
    'queue': {
        'dbdir': VEIL_VAR_DIR / 'queue',
        'configfile': VEIL_ETC_DIR / 'queue.conf',
        'port': DEFAULT_QUEUE_PORT
    },
    'resweb': {
        'config_file': VEIL_ETC_DIR / 'resweb.cfg',
        'queue_host': DEFAULT_QUEUE_HOST,
        'queue_port': DEFAULT_QUEUE_PORT,
        'server_host': 'localhost',
        'server_port': 5000
    },
    'supervisor': {
        'programs': {
            'queue': {
                'command': 'veil backend redis server up queue'
            },
            'resweb': {
                'command': 'resweb',
                'environment_variables': {
                    'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
                }
            },
            'delayed_job_scheduler': {
                'command': 'veil frontend pyres delayed-job-scheduler-up --host {host} --port {port}'.format(
                    host=DEFAULT_QUEUE_HOST,
                    port=DEFAULT_QUEUE_PORT
                )
            }
        }
    }
}
