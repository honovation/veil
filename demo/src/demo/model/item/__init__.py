import sandal.component

with sandal.component.init_component(__name__):
    from .item import create_item
    from .item import delete_item
    from .item import list_items
    from .item import EVENT_ITEM_CREATED
    from .item import EVENT_ITEM_DELETED
    from .counter import get_items_count

    EVENT_ITEM_CREATED = EVENT_ITEM_CREATED
    EVENT_ITEM_DELETED = EVENT_ITEM_DELETED

    __all__ = [
        # from item
        create_item.__name__,
        delete_item.__name__,
        list_items.__name__,
        'EVENT_ITEM_CREATED',
        'EVENT_ITEM_DELETED',
        # from counter
        get_items_count.__name__
    ]

    def init():
        from veil.model.event import subscribe_event
        from .counter import on_item_created
        from .counter import on_item_deleted

        subscribe_event(EVENT_ITEM_CREATED, on_item_created)
        subscribe_event(EVENT_ITEM_DELETED, on_item_deleted)

    init()