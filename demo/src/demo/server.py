from __future__ import unicode_literals, print_function, division
from veil.website import *
from sandal.template import *

@route('GET', '/', website='DEMO')
def home():
    return get_template('index.html').render()

@route('GET', '/item', website='DEMO')
@widget
def item():
    return get_template('item.html').render()




