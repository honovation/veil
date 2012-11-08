from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.backend.shell import *
import time
from fabric.colors import green

@script('deploy')
def deploy():
    print(green('veil down'))
    shell_execute('veil down')
    print(green('backup'))
    shell_execute('veil ljmall backup deploy_backup')
    print(green('veil install'))
    shell_execute('veil install')
    print(green('veil up --daemonize'))
    shell_execute('veil up --daemonize')
    print(green('veil migrate'))
    for i in range(3):
        try:
            shell_execute('veil migrate', capture=True)
        except:
            time.sleep(1)
    shell_execute('veil migrate', capture=True)

