from __future__ import unicode_literals, print_function, division
from sandal.collection import *
from sandal.binding import *
from sandal.command import *
from veil.database import *

demo_db = register_database('demo')

@command
@transactional(demo_db)
def create_item(name=not_empty):
    item_id = demo_db().insert('items', returns_id=True, name=name)
    return Item(item_id, name)


class Item(Entity):
    def __init__(self, id, name):
        super(Item, self).__init__(id=id, name=name)