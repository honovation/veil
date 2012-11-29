from __future__ import unicode_literals, print_function, division
import fabric.api
import datetime
import os
from veil.frontend.cli import *
from veil.environment import *

@script('backup-env')
def backup_env(backing_up_env):
    for veil_server_name in sorted(get_veil_servers(backing_up_env).keys()):
        bring_down_server(backing_up_env, veil_server_name)
    for veil_server_name in sorted(get_veil_servers(backing_up_env).keys()):
        backup_server(backing_up_env, veil_server_name)
    for veil_server_name in sorted(get_veil_servers(backing_up_env).keys()):
        bring_up_server(backing_up_env, veil_server_name)


def bring_down_server(backing_up_env, veil_server_name):
    deployed_via = get_remote_veil_server(backing_up_env, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} down'.format(backing_up_env, veil_server_name))


def bring_up_server(backing_up_env, veil_server_name):
    deployed_via = get_remote_veil_server(backing_up_env, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} up'.format(backing_up_env, veil_server_name))


def backup_server(backing_up_env, veil_server_name):
    deployed_via = get_remote_veil_server(backing_up_env, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    backup_path = '/backup/{}-{}-{}.tar.gz'.format(
        backing_up_env, veil_server_name,
        datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} backup {}'.format(
            backing_up_env, veil_server_name,
            backup_path))
    os.mkdir('/backup', mode=0755)
    fabric.api.get(backup_path, backup_path)