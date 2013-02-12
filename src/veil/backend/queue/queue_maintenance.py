from __future__ import unicode_literals, print_function, division
import pyres.failure
import pyres
import base64
from redis.client import Redis
from veil.frontend.cli import *
from .queue_client_installer import load_queue_client_config

@script('count-failed-jobs')
def count_failed_jobs(queue):
    count = 0
    for job in pyres.failure.all(get_resq(), 0, -1):
        if queue == job['queue']:
            count += 1
    print(count)


@script('delete-failed-jobs')
def delete_failed_jobs(queue):
    resq = get_resq()
    count = 0
    for job in pyres.failure.all(resq, 0, -1):
        if queue == job['queue']:
            pyres.failure.delete(resq, base64.decodestring(job['redis_value']))
            count += 1
    print(count)


@script('count-pending-jobs')
def count_pending_jobs(queue):
    resq = get_resq()
    count = resq.redis.llen('resque:queue:{}'.format(queue))
    print(count)


@script('delete-pending-jobs')
def delete_pending_jobs(queue):
    resq = get_resq()
    count = resq.redis.llen('resque:queue:{}'.format(queue))
    resq.redis.delete('resque:queue:{}'.format(queue))
    print(count)


def get_resq():
    config = load_queue_client_config()
    redis = Redis(host=config.host, port=config.port)
    resq = pyres.ResQ(server=redis)
    return resq
