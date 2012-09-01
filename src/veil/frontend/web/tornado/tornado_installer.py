from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *


@installation_script()
def install_tornado():
    install_python_package('tornado')