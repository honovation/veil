from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

@installation_script('install')
def install_postgresql_client():
    install_ubuntu_package('libpq-dev')
    install_python_package('psycopg2')