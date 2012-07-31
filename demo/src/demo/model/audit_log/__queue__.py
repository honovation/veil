from __future__ import unicode_literals, print_function, division
from sandal.clock import *
from veil.backend.queue import *
from .audit_log import create_audit_log

def on_item_created(item_id):
    require_queue().enqueue(
        create_audit_log_job,
        log='created item {}'.format(item_id),
        created_at=get_current_time())


def on_item_deleted(item_id):
    require_queue().enqueue(
        create_audit_log_job,
        log='deleted item {}'.format(item_id),
        created_at=get_current_time())


@job('demo')
def create_audit_log_job(log, created_at):
    create_audit_log(log, created_at)