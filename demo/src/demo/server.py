from __future__ import unicode_literals, print_function, division
from sandal.option import init_options
from veil.website import *
from sandal.template import *
from sandal.script import script

@route('GET', '/', website='DEMO')
def home():
    return get_template('index.html').render()






