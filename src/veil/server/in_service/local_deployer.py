from __future__ import unicode_literals, print_function, division
import logging
import threading
import functools
from veil.environment import get_current_veil_server
from veil.utility.shell import *
from veil.development.git import *
from veil.frontend.cli import *
from veil_component import VEIL_ENV
from veil_installer import *

LOGGER = logging.getLogger(__name__)


@script('deploy')
def deploy(start_after_deploy='TRUE'):
    is_local_env = VEIL_ENV.is_dev or VEIL_ENV.is_test
    if is_local_env:
        check_no_changes_not_committed()
        check_no_commits_not_pushed()
    shell_execute('veil install veil_installer.component_resource?veil.server.supervisor')
    shell_execute('sudo veil down' if is_local_env else 'sudo systemctl stop veil-server.service')
    shell_execute('veil install-server')
    if start_after_deploy == 'TRUE':
        shell_execute('sudo veil up --daemonize' if is_local_env else 'sudo systemctl start veil-server.service')
        shell_execute('veil migrate')
    if is_local_env:
        check_no_changes_not_committed()
        check_no_commits_not_pushed()


@script('patch')
def patch():
    shell_execute('veil migrate')
    threads = []
    current_veil_server = get_current_veil_server()
    server_specified_resources = current_veil_server.get('resources', [])
    for resource in server_specified_resources:
        if 'frontend_static_resource' in resource[0]:
            install_resource(resource)
    for program_name, program in current_veil_server.programs.items():
        if program.get('patchable'):
            program_name = '{}:{}'.format(program['group'], program_name) if program.get('group') else program_name
            thread = threading.Thread(target=functools.partial(shell_execute, 'veil server supervisor restart-program {}'.format(program_name)))
            threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
