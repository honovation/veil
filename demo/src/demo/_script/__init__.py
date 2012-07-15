from __future__ import unicode_literals, print_function, division
from sandal.option import init_options
from veil.website import *
from veil.environment import *
from sandal.script import *
from sandal.shell import *

@script('up')
def bring_up_demo():
    init_options({
        'logging': {
            'level': 'DEBUG'
        },
        'website': {
            'inline_static_files_directory': VEIL_LAYOUT.nginx.inline_static_files_directory,
            'external_static_files_directory': VEIL_LAYOUT.nginx.external_static_files_directory
        }
    })
    start_website(
        website='DEMO', port=8080, prevents_xsrf=False,
        master_template_dir = VEIL_HOME / 'src' / 'demo')

@script('install')
def install_demo():
    shell_execute('veil environment nginx install')
    shell_execute('veil environment supervisor install')
