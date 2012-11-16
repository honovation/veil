from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.cli import *
from veil.utility.shell import *

@script('migrate')
def migrate():
    for target, command in get_migration_commands().items():
        print('migrating {}...'.format(target))
        shell_execute(command)


@script('reset')
def reset():
    if VEIL_SERVER not in ['development', 'test']:
        raise Exception('{} environment must not reset'.format(VEIL_SERVER))
    for target, command in get_reset_commands().items():
        print('resetting {}...'.format(target))
        shell_execute(command)


def get_migration_commands():
    return get_settings().migration_commands


def get_reset_commands():
    return get_settings().reset_commands