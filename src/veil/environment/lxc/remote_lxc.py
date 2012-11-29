from __future__ import unicode_literals, print_function, division
import os
from veil.frontend.cli import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'remote_lxc_payload.py')

@script('provision-server')
def provision_server(provisioning_veil_env, provisioning_veil_server_name):
    raise NotImplementedError()