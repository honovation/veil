from __future__ import unicode_literals, print_function, division
import pyres.failure
import pyres
import base64
from redis.client import Redis
from veil.frontend.cli import *
from .queue_client_installer import queue_client_config


@script('count-failed-jobs')
def count_failed_jobs(queue=None):
    resq = get_resq()
    count = _count_failed_jobs(resq, queue)
    print(count)


def _count_failed_jobs(resq, queue):
    count = 0
    for job in pyres.failure.all(resq, 0, -1):
        if not queue or queue == job['queue']:
            count += 1
    return count


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
    count = get_resq().size(queue)
    print(count)


@script('delete-pending-jobs')
def delete_pending_jobs(queue):
    resq = get_resq()
    count = resq.size(queue)
    resq.redis.delete('resque:queue:{}'.format(queue))
    print(count)


@script('remove-queue')
def remove_queue(queue):
    resq = get_resq()
    if _count_failed_jobs(resq, queue):
        print('cannot remove queue with failed jobs')
        exit(-1)
    queue_job_list_key = 'resque:queue:{}'.format(queue)

    def _remove_queue(pipe):
        if pipe.llen(queue_job_list_key):
            print('cannot remove queue with pending jobs')
            exit(-1)
        pipe.multi()
        pipe.srem('resque:queues', queue)
        pipe.delete(queue_job_list_key)

    resq.redis.transaction(_remove_queue, queue_job_list_key)
    print('removed queue')


def get_resq():
    config = queue_client_config()
    redis = Redis(host=config.host, port=config.port)
    resq = pyres.ResQ(server=redis)
    return resq
