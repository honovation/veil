from __future__ import unicode_literals, print_function, division
import httplib
from sandal.template import *
from sandal.command import *
from veil.website import *
from veil.http import *
from .item import create_item
from .item import list_items
from .item import delete_item

@route('GET', '/', website='DEMO')
def home_page():
    return get_template('index.html').render()


@route('GET', '/resources/items', website='DEMO')
@widget
def list_items_widget():
    items = list_items()
    return get_template('list-items.html').render(items=items)


@widget
def list_items_element_widget(item):
    return get_template('list-items-element.html').render(item=item)


@widget
def new_item_widget(errors=None):
    command = command_for(create_item, errors)
    command.update(get_http_arguments())
    return get_template('new-item.html').render(**command)


@route('POST', '/resources/items', website='DEMO')
def create_item_action():
    http_arguments = get_http_arguments()
    try:
        create_item(**http_arguments)
    except InvalidCommand, e:
        set_http_status_code(httplib.BAD_REQUEST)
        return new_item_widget(e.errors)


@route('DELETE', '/resources/items/{{ id }}', id='\d+', website='DEMO')
def delete_item_action():
    id = get_http_argument('id')
    delete_item(id)



