from __future__ import unicode_literals, print_function, division
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
            'resweb_resource': {
                'resweb_host': resweb_host,
                'resweb_port': resweb_port,
                'queue_host': queue_host,
                'queue_port': queue_port
            }
        }
    })