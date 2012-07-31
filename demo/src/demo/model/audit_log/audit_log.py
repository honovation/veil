from __future__ import unicode_literals, print_function, division
from veil.profile.model import *

demo_db = register_database('demo')

def create_audit_log(log=not_empty):
    kwargs = dict(log=log, created_at=get_current_time())
    id = demo_db().insert('audit_logs', returns_id=True, **kwargs)
    return AuditLog(id, **kwargs)


class AuditLog(Entity):
    def __init__(self, id, log, created_at):
        super(AuditLog, self).__init__(id=id, log=log, created_at=created_at)
