######## export begin
from .item import create_item
from .item import delete_item
from .item import list_items
from .item import EVENT_ITEM_CREATED
from .item import EVENT_ITEM_DELETED

EVENT_ITEM_CREATED = EVENT_ITEM_CREATED
EVENT_ITEM_DELETED = EVENT_ITEM_DELETED

__all__ = [
    create_item.__name__,
    delete_item.__name__,
    list_items.__name__,
    'EVENT_ITEM_CREATED',
    'EVENT_ITEM_DELETED'
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()