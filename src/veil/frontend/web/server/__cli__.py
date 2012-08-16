from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *


@script('install')
def install_web_server():
    install_ubuntu_package('libxml2-dev')
    install_ubuntu_package('libxslt1-dev')
    install_python_package('lxml')