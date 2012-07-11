from veil.website import *
from sandal.template import *
from sandal.option import *

@route('GET', '/', website='demo')
def home():
    return get_template('index.html').render()

init_options({
    'logging': {
        'level': 'DEBUG'
    },
    'website': {

    }
})
start_website('demo', port=8080)