from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.backend.shell import *

migration_commands = set()

def register_migration_command(migration_command):
    migration_commands.add(migration_command)


@script('migrate')
def migrate():
    for command in migration_commands:
        shell_execute(command)