from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

from veil.environment.installation import *

@installation_script()
def install_deployment_component():
    install_python_package('Fabric', 'fabric')