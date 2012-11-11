from __future__ import unicode_literals, print_function, division

from veil_installer import *
from veil.environment import *

@composite_installer('queue_worker')
def install_queue_worker(name):
# TODO: cut down the dependency to only install component necessary for handling the queue
    return [], [component_resource(c) for c in get_application_components()]
