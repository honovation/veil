from __future__ import unicode_literals, print_function, division
import logging
from sandal.clock import *
from veil.backend.queue import *
from .audit_log import create_audit_log

LOGGER = logging.getLogger(__name__)

def on_item_created(item_id):
    current_time = get_current_time()
    LOGGER.debug('before created at: {}'.format(current_time))
    require_queue().enqueue(
        create_audit_log_job,
        log='created item {}'.format(item_id),
        created_at=current_time)


def on_item_deleted(item_id):
    require_queue().enqueue(
        create_audit_log_job,
        log='deleted item {}'.format(item_id),
        created_at=get_current_time())


@job('demo')
def create_audit_log_job(log, created_at):
    LOGGER.debug('after created at: {}'.format(created_at))
    create_audit_log(log, created_at)