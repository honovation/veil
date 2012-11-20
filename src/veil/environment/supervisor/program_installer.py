from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer('program')
def install_program(name):
    program = list_current_veil_server_programs()[name]
    return program.installer_providers, program.resources
