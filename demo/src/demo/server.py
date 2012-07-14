from __future__ import unicode_literals, print_function, division
from veil.website import *
from sandal.template import *
from sandal.script import script

@route('GET', '/', website='DEMO')
def home():
    return get_template('index.html').render()

@script('demo-web-up')
def bring_up_demo_website(*argv):
    start_website(website='DEMO', port=8080, prevents_xsrf=False)




