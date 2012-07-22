from __future__ import unicode_literals, print_function, division
from veil.website import *
from veil.database import *
from sandal.template import *

demo_db = register_database('demo')

@route('GET', '/', website='DEMO')
def home():
    return get_template('index.html').render()

@route('GET', '/item', website='DEMO')
@widget
def item():
    return get_template('item.html').render()

@route('GET', '/db', website='DEMO')
def query_db():
    return demo_db().list('SELECT * FROM items')




