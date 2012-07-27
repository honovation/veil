from __future__ import unicode_literals, print_function, division
import httplib
from sandal.template import *
from sandal.command import *
from veil.website import *
from veil.http import *
from . import item as impl

@route('GET', '/', website='DEMO')
def home():
    return get_template('index.html').render()


@route('GET', '/item', website='DEMO')
@widget
def item():
    return get_template('item.html').render()


@widget
def list_items():
    items = impl.list_items()
    return get_template('list-items.html').render(items=items)


@widget
def new_item(errors=None):
    command = command_for(impl.create_item, errors)
    command.update(get_http_arguments())
    return get_template('new-item.html').render(**command)


@route('POST', '/resources/items', website='DEMO')
def create_item():
    http_arguments = get_http_arguments()
    try:
        impl.create_item(**http_arguments)
    except InvalidCommand, e:
        set_http_status_code(httplib.BAD_REQUEST)
        return new_item(e.errors)




