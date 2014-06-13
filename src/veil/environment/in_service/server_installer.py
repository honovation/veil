from __future__ import unicode_literals, print_function, division
import fabric.api
import fabric.contrib.files
from veil_installer import *


@composite_installer
def veil_servers_resource(servers, action):
    return [veil_server_resource(server=server, action=action) for server in servers]


@atomic_installer
def veil_server_resource(server, action='PATCH'):
    if action not in ('DEPLOY', 'PATCH'):
        raise Exception('unknown action: {}'.format(action))

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['veil_server?{}'.format(server.container_name)] = action
        return

    fabric.api.env.host_string = server.deploys_via
    fabric.api.env.forward_agent = True
    with fabric.api.cd(server.veil_home):
        if 'DEPLOY' == action:
            fabric.api.sudo('{}/bin/veil :{} deploy'.format(server.veil_framework_home, server.fullname))
            fabric.api.sudo('touch {}'.format(server.deployed_tag_path))
        else:  # PATCH
            fabric.api.sudo('{}/bin/veil :{} patch'.format(server.veil_framework_home, server.fullname))
            fabric.api.sudo('touch {}'.format(server.patched_tag_path))
