from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.frontend.cli import *
from veil.backend.shell import *
import time

@script('deploy')
def deploy():
    if VEIL_VAR_DIR.exists():
        shell_execute('veil down')
        shell_execute('veil ljmall backup deploy_backup')
    shell_execute('veil install')
    shell_execute('veil up --daemonize')
    for i in range(3):
        try:
            shell_execute('veil migrate', capture=True)
        except:
            time.sleep(1)
    shell_execute('veil migrate', capture=True)

