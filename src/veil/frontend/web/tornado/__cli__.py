from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *


@script('install')
def install_tornado():
    install_python_package('tornado')
    execute_script('frontend', 'encoding', 'install')