from __future__ import unicode_literals, print_function, division
import logging
import argparse
import time
import sys
from veil_component import is_recording_dynamic_dependencies, load_all_components
from veil.environment import *
from veil.utility.shell import *
from veil.frontend.cli import script
from .supervisorctl import supervisorctl
from .supervisorctl import is_supervisord_running

LOGGER = logging.getLogger(__name__)

@script('up')
def bring_up_programs(*argv):
    # create socket directory for postgresql if not exists
    try:
        shell_execute('getent passwd postgres')
    except ShellExecutionError:
        pass
    else:
        shell_execute('install -d -m 2775 -o postgres -g postgres /var/run/postgresql')
    if 1 == len(argv) and not argv[0].startswith('--'):
        bring_up_program(argv[0])
    else:
        bring_up_supervisor(*argv)


def bring_up_program(program_name):
    config = get_current_veil_server().programs[program_name]
    execute_command = config.execute_command
    LOGGER.info(execute_command)
    pass_control_to(execute_command)


def bring_up_supervisor(*argv):
    argument_parser = argparse.ArgumentParser('Bring up the application')
    argument_parser.add_argument('--daemonize', action='store_true', help='should the process run in background')
    args = argument_parser.parse_args(argv)

    daemonize = args.daemonize
    if daemonize:
        shell_execute('supervisord -c {}'.format(VEIL_ETC_DIR / 'supervisor.cfg'))
        for i in range(30):
            supervisor_status = supervisorctl('status', capture=True)
            lines = [line for line in supervisor_status.splitlines() if line.strip()]
            if all('RUNNING' in line for line in lines):
                return
            if any('FATAL' in line for line in lines):
                break
            time.sleep(5)
        LOGGER.info('failed to bring up supervisor: latest status: %(status)s', {
            'status': supervisor_status
        })
        sys.exit(1)
    else:
        if VEIL_ENV.is_dev or VEIL_ENV.is_test:
            update_dynamic_dependencies()
        pass_control_to('supervisord -n -c {}'.format(VEIL_ETC_DIR / 'supervisor.cfg'))


@script('update-dynamic-dependencies')
def update_dynamic_dependencies():
    if not is_recording_dynamic_dependencies():
        LOGGER.warn('cannot update dynamic dependencies because the recording is not started yet')
        return
    try:
        load_all_components() # import module will execute a lot record_dynamic_dependency_provider
    except Exception:
        pass


@script('down')
def bring_down_supervisor():
    if not is_supervisord_running():
        return
    supervisorctl('shutdown')
    while is_supervisord_running():
        time.sleep(3)


@script('restart-program')
def restart_program(program_name):
    supervisorctl('restart', program_name)
