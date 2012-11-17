from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.frontend.cli import *
from veil.utility.shell import *

@script('migrate')
def migrate():
    for target, command in get_migration_commands().items():
        print('migrating {}...'.format(target))
        shell_execute(command)


def get_migration_commands():
    return get_settings().migration_commands