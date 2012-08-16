from __future__ import unicode_literals, print_function, division
from veil.environment.deployment import *
from veil.environment.installation import *

@installation_script()
def install():
    install_python_package('jinja2')
    install_python_package('markupsafe')