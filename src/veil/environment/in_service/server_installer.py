from __future__ import unicode_literals, print_function, division
import os
import fabric.api
import fabric.state
from veil_installer import *
from veil.environment import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'server_installer_payload.py')

@composite_installer
def veil_env_servers_resource(veil_env_name, is_patch=False):
    resources = []
    for veil_server_name in sorted(list_veil_servers(veil_env_name).keys()):
        resources.append(veil_server_resource(
            veil_env_name=veil_env_name, veil_server_name=veil_server_name, is_patch=is_patch))
    return resources


@atomic_installer
def veil_server_resource(veil_env_name, veil_server_name, is_patch=False):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['veil_server?{}-{}'.format(veil_env_name, veil_server_name)] = 'INSTALL'
        return
    fabric.state.env.host_string = get_veil_server_deploys_via(veil_env_name, veil_server_name)
    fabric.state.env.forward_agent = True
    fabric.api.put(PAYLOAD, '/opt/server_installer_payload.py', use_sudo=True, mode=0600)
    fabric.api.sudo('python /opt/server_installer_payload.py {} {} {} {}'.format(
        get_application_codebase(),
        veil_env_name,
        veil_server_name,
        'patch' if is_patch else 'deploy'))

