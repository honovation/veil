from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

from veil.environment.setting import *
from veil.environment.installation import *

@installation_script()
def install():
    install_python_package('jinja2')
    install_python_package('markupsafe')