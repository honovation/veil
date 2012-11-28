from __future__ import unicode_literals, print_function, division
import logging
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@script('deploy')
def deploy():
    shell_execute('veil install veil_installer.component_resource?veil.environment.supervisor')
    shell_execute('veil down')
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')