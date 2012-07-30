from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *

def install_python_package(package_name, test_package=None):
    test_package = test_package or package_name
    try:
        __import__(test_package)
    except ImportError:
        shell_execute('pip install {}'.format(package_name))