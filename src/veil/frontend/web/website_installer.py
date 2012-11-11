from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil_installer import *

@composite_installer('website')
def install_website(name):
# TODO: cut down the dependency to only install component necessary for handling the queue
    return [], [component_resource(c) for c in get_application_components()]
