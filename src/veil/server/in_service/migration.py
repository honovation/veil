from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@script('migrate')
def migrate():
    for program_name, command in get_migration_commands().items():
        LOGGER.info('migrating {}...'.format(program_name))
        shell_execute(command)


def get_migration_commands():
    migrate_commands = {}
    for program_name, program in get_current_veil_server().programs.items():
        if program.get('migrate_command'):
            migrate_commands[program_name] = program.migrate_command
    return migrate_commands