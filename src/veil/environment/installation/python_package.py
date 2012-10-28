from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.backend.shell import *

LOGGER = logging.getLogger(__name__)

def install_python_package(package_name, test_package=None, **kwargs):
    kwargs['capture'] = True
    test_package = test_package or package_name
    try:
        __import__(test_package)
    except ImportError:
        LOGGER.info('installing python package {} ...'.format(package_name))
#        mirror = os.getenv('VEIL_PYTHON_PACKAGE_MIRROR', 'http://dependency-veil.googlecode.com/svn/trunk/')
        mirror = os.getenv('VEIL_PYTHON_PACKAGE_MIRROR', 'http://200.200.200.25:8080/')
        if mirror:
            shell_execute('pip install {} --no-index -f {}'.format(package_name, mirror), **kwargs)
        else:
            shell_execute('pip install {}'.format(package_name), **kwargs)