from __future__ import unicode_literals, print_function, division
import os
import fabric.api
import fabric.contrib.files
from veil.environment import *
from veil_installer import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'server_installer_payload.py')
veil_servers_with_payload_uploaded = []


@composite_installer
def veil_servers_resource(veil_env_name, action):
    resources = []
    for veil_server_name in reversed(list_veil_server_names(veil_env_name)):
        resources.append(veil_server_resource(veil_env_name=veil_env_name, veil_server_name=veil_server_name, action=action))
    return resources


@atomic_installer
def veil_server_resource(veil_env_name, veil_server_name, action='PATCH'):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['veil_server?{}-{}'.format(veil_env_name, veil_server_name)] = 'INSTALL'
        return
    fabric.api.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.api.env.forward_agent = True
    if fabric.api.env.host_string not in veil_servers_with_payload_uploaded:
        fabric.api.put(PAYLOAD, '/opt/server_installer_payload.py', use_sudo=True, mode=0600)
        veil_servers_with_payload_uploaded.append(fabric.api.env.host_string)
    fabric.api.sudo('python /opt/server_installer_payload.py {} {} {} {} {}'.format(VEIL_FRAMEWORK_CODEBASE, get_application_codebase(),
        veil_env_name, veil_server_name, action))
