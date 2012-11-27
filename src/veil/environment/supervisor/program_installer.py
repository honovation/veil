from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer
def program_resource(name):
    program = get_current_veil_server().programs[name]
    return program.resources
