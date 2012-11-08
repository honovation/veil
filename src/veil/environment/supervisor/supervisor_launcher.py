from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
import time
from veil.backend.shell import *
from veil.environment.setting import *
from veil.frontend.cli import script
from .supervisorctl import are_all_supervisord_programs_running
from .supervisorctl import supervisorctl
from .supervisorctl import is_supervisord_running

@script('up')
def bring_up_programs(*argv):
    if 1 == len(argv) and not argv[0].startswith('--'):
        bring_up_program(argv[0])
    else:
        bring_up_supervisor(*argv)


def bring_up_program(program_name):
    config = get_settings().supervisor
    execute_command = config.programs[program_name].execute_command
    print(execute_command)
    pass_control_to(execute_command)


def bring_up_supervisor(*argv):
    argument_parser = ArgumentParser('Bring up the application')
    argument_parser.add_argument('--daemonize', action='store_true',
        help='should the process run in background')
    args = argument_parser.parse_args(argv)

    config = get_settings().supervisor
    daemonize = args.daemonize or config.daemonize
    if daemonize:
        shell_execute('supervisord -c {}'.format(config.config_file))
        for i in range(10):
            if are_all_supervisord_programs_running():
                return
            time.sleep(3)
        print('failed to bring up supervisor, latest status: {}'.format(supervisorctl('status', capture=True)))
    else:
        pass_control_to('supervisord -n -c {}'.format(config.config_file))


@script('down')
def bring_down_supervisor():
    supervisorctl('shutdown')
    while is_supervisord_running():
        time.sleep(3)



