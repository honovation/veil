from __future__ import unicode_literals, print_function, division
from veil.profile.model import *
from veil.model.event import *

demo_db = register_database('demo')
EVENT_ITEM_CREATED = 'item-created'
EVENT_ITEM_DELETED = 'item-deleted'

@transactional(demo_db)
@command
def create_item(name=not_empty):
    id = demo_db().insert('items', returns_id=True, name=name)
    publish_event(EVENT_ITEM_CREATED, item_id=id)
    return Item(id, name, None)


def list_items():
    rows = demo_db().list('SELECT * FROM items')
    return [Item(**row) for row in rows]


def get_item(id):
    row = demo_db().get('SELECT * FROM items WHERE id=%(id)s', id=id)
    return Item(**row)


def delete_item(id):
    rows_count = demo_db().execute('DELETE FROM items WHERE id=%(id)s', id=id)
    if rows_count:
        publish_event(EVENT_ITEM_DELETED, item_id=id)
    else:
        raise NotFoundError('no contact attribute definition deleted')


def count_items():
    return demo_db().get_scalar('SELECT COUNT(*) FROM items')


class Item(Entity):
    def __init__(self, id, name, image_url):
        super(Item, self).__init__(id=id, name=name, image_url=image_url)