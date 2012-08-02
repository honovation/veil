import sandal.component

with sandal.component.init_component(__name__):
    from .audit_log import list_audit_logs

    __all__ = [
        list_audit_logs.__name__
    ]

    def init():
        from veil.model.event import subscribe_event
        from demo.model.item import EVENT_ITEM_CREATED
        from demo.model.item import EVENT_ITEM_DELETED
        from .__queue__ import on_item_created
        from .__queue__ import on_item_deleted

        subscribe_event(EVENT_ITEM_CREATED, on_item_created)
        subscribe_event(EVENT_ITEM_DELETED, on_item_deleted)

    init()