from __future__ import unicode_literals, print_function, division
import logging
from veil.frontend.cli import *
from veil.utility.shell import *
from veil.environment import *

LOGGER = logging.getLogger(__name__)

@script('deploy')
def deploy():
    shell_execute('veil install veil_installer.component_resource?veil.server.supervisor')
    shell_execute('veil down')
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')

@script('patch')
def patch():
    shell_execute('veil migrate')
    for program_name, program in get_current_veil_server().programs.items():
        if program.get('patchable'):
            program_name = '{}:{}'.format(program['group'], program_name) if program.get('group') else program_name
            shell_execute('veil server supervisor restart-program {}'.format(program_name))