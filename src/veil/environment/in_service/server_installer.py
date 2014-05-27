from __future__ import unicode_literals, print_function, division
import os
import tempfile
import time
import fabric.api
import fabric.contrib.files
from veil_component import as_path
from veil_installer import *
from veil.environment import *
from veil.server.config import *

PAYLOAD = os.path.join(os.path.dirname(__file__), 'server_installer_payload.py')
veil_servers_with_payload_uploaded = []


@composite_installer
def veil_env_servers_resource(veil_env_name, action='PATCH'):
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
    while fabric.contrib.files.exists('/etc/network/if-up.d/veil-server-init'):
        print('waiting for veil server initialization: {}'.format(veil_server_name))
        time.sleep(2)
    if not fabric.contrib.files.exists('/etc/network/if-up.d/veil-server-init'):
        print('veil server initialization has finished')
    fabric.api.sudo('python /opt/server_installer_payload.py {} {} {} {} {}'.format(VEIL_FRAMEWORK_CODEBASE, get_application_codebase(),
        veil_env_name, veil_server_name, action))
    if action == 'DEPLOY':
        remote_install_boot_script(veil_env_name, veil_server_name)


def remote_install_boot_script(veil_env_name, veil_server_name):
    boot_script_name = '{}-{}'.format(veil_env_name, veil_server_name)
    print('install boot script: {} ...'.format(boot_script_name))
    boot_script_path = '/etc/init.d/{}'.format(boot_script_name)
    fabric.api.sudo('update-rc.d -f {} remove'.format(boot_script_name))
    temp_file_path = as_path(tempfile.mktemp())
    temp_file_path.write_text(render_boot_script(boot_script_name, veil_env_name, veil_server_name))
    fabric.api.put(temp_file_path, boot_script_path, use_sudo=True, mode=0755)
    fabric.api.sudo('chown root:root {}'.format(boot_script_path))
    fabric.api.sudo('update-rc.d {} defaults 90 10'.format(boot_script_name))


def render_boot_script(script_name, veil_env_name, veil_server_name):
    return render_config('veil-server-boot-script.j2', script_name=script_name,
        do_start_command='cd /opt/{}/app && sudo veil :{}/{} up --daemonize'.format(veil_env_name, veil_env_name, veil_server_name),
        do_stop_command='cd /opt/{}/app && sudo veil :{}/{} down'.format(veil_env_name, veil_env_name, veil_server_name))
