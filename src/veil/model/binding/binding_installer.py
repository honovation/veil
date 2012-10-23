from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

from veil.environment.installation import *

@installation_script()
def install():
    install_python_package('python-dateutil', 'dateutil')
    install_python_package('pytz')
