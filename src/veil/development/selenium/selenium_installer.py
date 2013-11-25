# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.server.python import *

@atomic_installer
def selenium_python_package_resource():
    install_resource(python_package_resource(name='selenium'))