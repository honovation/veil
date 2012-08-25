from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

@installation_script()
def install():
    install_python_package('python-dateutil')
    install_python_package('pytz')
