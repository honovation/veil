from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *


@script('install')
def install_queue_client():
    install_ubuntu_package('python2.7-dev')
    execute_script('backend', 'redis', 'client', 'install')
    install_python_package('pyres')
