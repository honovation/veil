from __future__ import unicode_literals, print_function, division
from veil.environment.deployment import *
from veil.frontend.cli import *

@script('install')
def install_encoding_support():
    install_python_package('chardet')