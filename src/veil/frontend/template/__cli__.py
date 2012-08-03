from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *

@script('install')
def install_template():
    install_python_package('jinja2')
    install_python_package('markupsafe')