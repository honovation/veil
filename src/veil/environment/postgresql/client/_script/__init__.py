from __future__ import unicode_literals, print_function, division
from sandal.script import *
from ....ubuntu import install_ubuntu_package
from ....python import install_python_package

@script('install')
def install_postgresql_client():
    install_ubuntu_package('libpq-dev')
    install_python_package('psycopg2')