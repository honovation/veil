from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

@script('migrate')
def migrate():
    for program_name, command in get_migration_commands().items():
        print('migrating {}...'.format(program_name))
        shell_execute(command)


def get_migration_commands():
    migrate_commands = {}
    for program_name, program in list_current_veil_server_programs().items():
        if program.get('migrate_command'):
            migrate_commands[program_name] = program.migrate_command
    return migrate_commands