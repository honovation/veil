from __future__ import unicode_literals, print_function, division
from sandal.shell import *
from veil.web.server import *
from veil.environment import *
from veil.script import *

@script('up')
def bring_up_demo():
    start_website(
        website='DEMO', port=8080, prevents_xsrf=False,
        master_template_dir = VEIL_HOME / 'src' / 'demo')

@script('install')
def install_demo():
    shell_execute('veil environment veil-cfg generate')
    shell_execute('veil environment nginx install')
    shell_execute('veil database client postgresql install')
    shell_execute('veil database server postgresql install')
    shell_execute('veil environment supervisor install')
