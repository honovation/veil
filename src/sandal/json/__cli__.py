from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *
from veil.environment.deployment import *

@installation_script()
def install():
    install_python_package('python-dateutil')
