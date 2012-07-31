from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from demo.model.item import *
from demo.model.audit_log import *

@route('GET', '/')
def home_page():
    return get_template('index.html').render()


@route('GET', '/resources/items')
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


@route('POST', '/resources/items')
def create_item_action():
    http_arguments = get_http_arguments()
    try:
        create_item(**http_arguments)
    except InvalidCommand, e:
        set_http_status_code(httplib.BAD_REQUEST)
        return new_item_widget(e.errors)


@route('DELETE', '/resources/items/{{ id }}', id='\d+')
def delete_item_action():
    id = get_http_argument('id')
    delete_item(id)


@route('GET', '/resources/audit-logs')
@widget
def list_audit_logs_widget():
    audit_logs = list_audit_logs()
    return get_template('list-audit-logs.html').render(audit_logs=audit_logs)



