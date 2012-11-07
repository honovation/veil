from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil_installer import *

@installer('website')
def install_website(dry_run_result, name):
# TODO: cut down the dependency to only install component necessary for handling the queue
    return [], [component_resource(c) for c in get_application_components()]
