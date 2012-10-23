from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

from veil.environment.installation import *

@installation_script()
def install_queue_api():
    install_python_package('pytz')
    install_python_package('pyres')
    install_python_package('croniter')