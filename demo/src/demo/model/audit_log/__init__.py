######## export begin
from .audit_log import list_audit_logs

__all__ = [
    list_audit_logs.__name__
]
######## export end

def init():
    from veil.component import init_component
    from veil.model.event import subscribe_event
    from demo.model.item import EVENT_ITEM_CREATED
    from demo.model.item import EVENT_ITEM_DELETED
    from .audit_log import on_item_created
    from .audit_log import on_item_deleted

    init_component(__name__)
    subscribe_event(EVENT_ITEM_CREATED, on_item_created)
    subscribe_event(EVENT_ITEM_DELETED, on_item_deleted)

init()