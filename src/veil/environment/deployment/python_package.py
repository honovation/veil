from __future__ import unicode_literals, print_function, division
import os
from veil.backend.shell import *

def install_python_package(package_name, test_package=None):
    test_package = test_package or package_name
    try:
        __import__(test_package)
    except ImportError:
        mirror = os.getenv('VEIL_PYTHON_PACKAGE_MIRROR')
        if mirror:
            shell_execute('pip install {} --no-index -f {}'.format(package_name, mirror))
        else:
            shell_execute('pip install {}'.format(package_name))