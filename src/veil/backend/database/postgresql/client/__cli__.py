from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *

@script('install')
def install_postgresql_client():
    install_ubuntu_package('libpq-dev')
    install_python_package('psycopg2')