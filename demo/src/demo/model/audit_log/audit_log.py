from __future__ import unicode_literals, print_function, division
from veil.profile.model import *

demo_db = register_database('demo')

def create_audit_log(log=not_empty, created_at=optional()):
    kwargs = dict(log=log, created_at=created_at or get_current_time())
    id = demo_db().insert('audit_logs', returns_id=True, **kwargs)
    return AuditLog(id, **kwargs)

def list_audit_logs():
    rows = demo_db().list('SELECT * FROM audit_logs ORDER BY created_at DESC')
    return [AuditLog(**row) for row in rows]


class AuditLog(Entity):
    def __init__(self, id, log, created_at):
        super(AuditLog, self).__init__(id=id, log=log, created_at=created_at)
