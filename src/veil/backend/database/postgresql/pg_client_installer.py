from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

from veil.environment.installation import *

@installation_script()
def install_postgresql_client():
    install_ubuntu_package('libpq-dev')
    install_python_package('psycopg2')