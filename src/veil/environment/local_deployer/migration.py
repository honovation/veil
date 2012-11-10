from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.frontend.cli import *
from veil.backend.shell import *

migration_commands = set()
reset_commands = set()

def register_migration_command(migration_command):
    migration_commands.add(migration_command)


def register_reset_command(reset_command):
    reset_commands.add(reset_command)


@script('migrate')
def migrate():
    for command in migration_commands:
        shell_execute(command)


@script('reset')
def reset():
    if VEIL_SERVER not in ['development', 'test']:
        raise Exception('{} environment must not reset'.format(VEIL_SERVER))
    for command in reset_commands:
        shell_execute(command)