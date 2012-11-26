from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@script('deploy')
def deploy():
    shell_execute('veil install component?veil.environment.supervisor')
    shell_execute('veil down')
    shell_execute('veil install component?ljmall')
    shell_execute('veil ljmall backup deploy_backup')
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')