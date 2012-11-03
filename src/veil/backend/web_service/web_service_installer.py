from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

@installation_script()
def install_web_service_component():
    install_python_package('suds')

