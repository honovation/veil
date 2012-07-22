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
            'inline_static_files_directory': NGINX_BASE_SETTINGS.nginx.inline_static_files_directory,
            'external_static_files_directory': NGINX_BASE_SETTINGS.nginx.external_static_files_directory
        },
        'database': {
            'type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'db_name': 'demo',
            'user': 'veil',
            'password': 'p@55word'
        }
    })
    start_website(
        website='DEMO', port=8080, prevents_xsrf=False,
        master_template_dir = VEIL_HOME / 'src' / 'demo')

@script('install')
def install_demo():
    shell_execute('veil environment nginx install')
    shell_execute('veil environment postgresql client install')
    shell_execute('veil environment postgresql server install')
    shell_execute('veil environment supervisor install')
