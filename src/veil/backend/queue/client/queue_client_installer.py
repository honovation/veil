from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.installation import *


@installation_script()
def install_queue_client():
    install_ubuntu_package('python2.7-dev')
    install_python_package('pytz')
    install_python_package('pyres')
