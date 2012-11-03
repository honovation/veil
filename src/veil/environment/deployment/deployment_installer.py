from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

@installation_script()
def install_deployment_component():
    install_python_package('Fabric', 'fabric')