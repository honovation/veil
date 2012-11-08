from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.backend.shell import *

@script('deploy')
def deploy():
    print('veil down...')
    shell_execute('veil down')
    print('[DEPLOY] install...')
    shell_execute('veil install')
    print('[DEPLOY] bringing up...')
    shell_execute('veil up --daemonize')
    wait_for_application_up_then_migrate()


def wait_for_application_up_then_migrate():
    print('[DEPLOY] migrating...')
    for i in range(3):
        try:
            output = shell_execute('veil migrate', capture=True)
            print(output, end='')
            print('[DEPLOY] migrated')
            return
        except:
            print('[DEPLOY] application not up yet, retrying migration...')
    print('[DEPLOY] retry migration for the last time')
    shell_execute('veil migrate')
    print('[DEPLOY] migrated')
