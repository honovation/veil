from __future__ import unicode_literals, print_function, division
from veil.frontend.script import *
from veil.environment.deployment import *


@script('install')
def install_pyres():
    install_ubuntu_package('python2.7-dev')
    execute_script('backend', 'redis', 'client', 'install')
    install_python_package('pyres')
    install_python_package('croniter')