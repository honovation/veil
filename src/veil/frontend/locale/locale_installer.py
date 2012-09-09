from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

@installation_script()
def install_locale_support():
    install_python_package('babel')
