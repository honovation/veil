from __future__ import unicode_literals, print_function, division
import os
import fabric.api
import fabric.contrib.files
from veil.environment import *
from veil_installer import *
from veil.utility.shell import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'server_installer_payload.py')
REMOTE_PAYLOAD_PATH = HOST_SHARE_DIR / 'server_installer_payload.py'
hosts_with_payload_uploaded = []


@composite_installer
def veil_servers_resource(veil_env_name, action):
    resources = []
    for veil_server_name in reversed(list_veil_server_names(veil_env_name)):
        resources.append(veil_server_resource(server=get_veil_server(veil_env_name, veil_server_name), action=action))
    return resources


@atomic_installer
def veil_server_resource(server, action='PATCH'):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['veil_server?{}'.format(server.container_name)] = 'INSTALL'
        return
    fabric.api.env.host_string = server.deploys_via
    fabric.api.env.forward_agent = True
    if server.host_base_name not in hosts_with_payload_uploaded:
        fabric.api.put(PAYLOAD, REMOTE_PAYLOAD_PATH, use_sudo=True, mode=0600)
        hosts_with_payload_uploaded.append(server.host_base_name)
    fabric.api.sudo('python {} {} {} {} {} {}'.format(REMOTE_PAYLOAD_PATH, VEIL_FRAMEWORK_CODEBASE, get_application_codebase(),
        server.env_name, server.name, action))
    if 'DEPLOY' == action:
        shell_execute('touch {}'.format(server.deployed_tag_path), capture=True, debug=True)
    else:  # PATCH
        shell_execute('touch {}'.format(server.patched_tag_path), capture=True, debug=True)
