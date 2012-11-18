from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.backend.new_redis_setting import redis_program

def queue_program(host, port):
    return objectify({
        'queue': redis_program('queue', host, port).queue_redis
    })