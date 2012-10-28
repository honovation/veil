from __future__ import unicode_literals, print_function, division
import sys
from veil.frontend.cli import *
from veil.supervisor import *
from veil.backend.shell import *

migration_commands = set()

def register_migration_command(migration_command):
    migration_commands.add(migration_command)


@script('migrate')
def migrate():
    for command in migration_commands:
        shell_execute(command)


@script('deploy')
def deploy():
    if is_supervisord_running():
        print('[DEPLOY] supervisord is running, doing hot deploy...')
        hot_deploy()
    else:
        print('[DEPLOY] supervisord is not running, doing cold deploy...')
        cold_deploy()


def hot_deploy():
    print('[DEPLOY] stopping all programs...')
    supervisorctl('stop all')
    print('[DEPLOY] install...')
    shell_execute('veil install')
    print('[DEPLOY] updating program list...')
    supervisorctl('update')
    wait_for_application_up_then_migrate()
    print('[DEPLOY] starting all programs...')
    supervisorctl('start all')


def cold_deploy():
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
