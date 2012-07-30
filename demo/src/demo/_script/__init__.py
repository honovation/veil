from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.frontend.web.server import *
from veil.frontend.script import *

@script('up')
def bring_up_demo():
    start_website(website='DEMO')

@script('install')
def install_demo():
    shell_execute('veil environment runtime config-file generate')
    shell_execute('veil environment runtime supervisor install')
    shell_execute('veil frontend web nginx install')
    shell_execute('veil backend rdbms postgresql client install')
    shell_execute('veil backend rdbms postgresql server install')
    shell_execute('veil backend redis client install')
    shell_execute('veil backend redis server install')
