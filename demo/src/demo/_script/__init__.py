from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.frontend.web.server import *
from veil.environment.layout import *
from veil.frontend.script import *

@script('up')
def bring_up_demo():
    start_website(
        website='DEMO', port=8080, prevents_xsrf=False,
        master_template_dir = VEIL_HOME / 'src' / 'demo')

@script('install')
def install_demo():
    shell_execute('veil generate-configuration')
    shell_execute('veil web nginx install')
    shell_execute('veil database postgresql client install')
    shell_execute('veil database postgresql server install')
    shell_execute('veil supervisor install')
