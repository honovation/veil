from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.utility.shell import *

@script('deploy')
def deploy():
    shell_execute('veil install-supervisor')
    shell_execute('veil down')
    shell_execute('veil install-component ljmall')
    shell_execute('veil ljmall backup deploy_backup')
    shell_execute('veil install')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')
