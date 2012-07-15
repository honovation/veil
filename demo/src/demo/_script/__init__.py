from __future__ import unicode_literals, print_function, division
from sandal.option import init_options
from veil.website import *
from sandal.script import *
from sandal.shell import *

@script('up')
def bring_up_demo():
    init_options({
        'logging': {
            'level': 'DEBUG'
        },
        'website': {

        }
    })
    start_website(website='DEMO', port=8080, prevents_xsrf=False)

@script('install')
def install_demo():
    shell_execute('veil environment nginx install')
    shell_execute('veil environment supervisor install')
