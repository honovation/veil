from __future__ import unicode_literals, print_function, division
import fabric.api
import datetime
import os
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *


@script('create')
def create_env_backup(backing_up_env):
    return do_install(env_backup_resource(backing_up_env=backing_up_env))


@atomic_installer
def env_backup_resource(backing_up_env):
    for veil_server_name in sorted(list_veil_servers(backing_up_env).keys()):
        bring_down_server(backing_up_env, veil_server_name)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    for veil_server_name in sorted(list_veil_servers(backing_up_env).keys()):
        if '@guard' != veil_server_name:
            backup_server(backing_up_env, veil_server_name, timestamp)
    for veil_server_name in sorted(list_veil_servers(backing_up_env).keys()):
        bring_up_server(backing_up_env, veil_server_name)


def bring_down_server(backing_up_env, veil_server_name):
    deployed_via = get_veil_server_host_string(backing_up_env, veil_server_name)
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} down'.format(backing_up_env, veil_server_name))


def bring_up_server(backing_up_env, veil_server_name):
    deployed_via = get_veil_server_host_string(backing_up_env, veil_server_name)
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} up --daemonize'.format(backing_up_env, veil_server_name))


def backup_server(backing_up_env, veil_server_name, timestamp):
    deployed_via = get_veil_server_host_string(backing_up_env, veil_server_name)
    fabric.api.env.host_string = deployed_via
    backup_path = '/backup/{}-{}-{}.tar.gz'.format(
        backing_up_env, veil_server_name, timestamp)
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} backup {}'.format(
            backing_up_env, veil_server_name,
            backup_path))
    if not os.path.exists('/backup'):
        os.mkdir('/backup', 0755)
    fabric.api.get(backup_path, backup_path)