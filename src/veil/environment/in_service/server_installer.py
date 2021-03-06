from __future__ import unicode_literals, print_function, division
import fabric.api
import fabric.contrib.files
from veil_component import *
from veil.environment import *
from veil.environment.lxd import *
from veil_installer import *
from .env_config_dir import get_env_config_dir


@composite_installer
def veil_servers_resource(servers, action, start_after_deploy=True):
    return [veil_server_resource(server=server, action=action, start_after_deploy=start_after_deploy) for server in servers]


@atomic_installer
def veil_server_resource(server, action='PATCH', start_after_deploy=True):
    if action not in ('DEPLOY', 'PATCH'):
        raise Exception('unknown action: {}'.format(action))

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['veil_server?{}'.format(server.container_name)] = action
        return

    if not is_container_running(server):
        print(yellow('Skipped {} server {} as its container is not running'.format(action, server.container_name)))

    with fabric.api.settings(host_string=server.deploys_via, user=server.ssh_user, port=server.ssh_port, disable_known_hosts=True):
        with fabric.api.cd(server.veil_home):
            print(cyan('{} server {} ...'.format(action, server.name)))
            if 'DEPLOY' == action:
                fabric.api.run('{}/bin/veil :{} deploy {}'.format(server.veil_framework_home, server.fullname, 'TRUE' if start_after_deploy else 'FALSE'))
                fabric.api.run('touch {}'.format(server.deployed_tag_path))
            else:  # PATCH
                fabric.api.run('{}/bin/veil :{} patch'.format(server.veil_framework_home, server.fullname))
                fabric.api.run('touch {}'.format(server.patched_tag_path))


def is_container_running(server):
    container = LXDClient(endpoint=server.lxd_endpoint, config_dir=get_env_config_dir()).get_container(server.container_name)
    return container and container.running


def is_server_running(server, on_host=True):
    if on_host:
        ret = fabric.api.run('ps -ef | grep supervisord | grep -e {}/supervisor.cfg | grep -v grep'.format(server.etc_dir), warn_only=True)
    else:
        host = get_veil_host(server.VEIL_ENV.name, server.host_name)
        with fabric.api.settings(host_string=host.deploys_via, user=host.ssh_user, port=host.ssh_port):
            ret = fabric.api.run('ps -ef | grep supervisord | grep -e {}/supervisor.cfg | grep -v grep'.format(server.etc_dir), warn_only=True)
    return ret.return_code == 0
