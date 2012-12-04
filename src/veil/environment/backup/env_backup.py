from __future__ import unicode_literals, print_function, division
import fabric.api
import datetime
import os
from veil_installer import *
from veil.frontend.cli import *
from veil.environment import *


@script('create')
def create_env_backup():
    return install_resource(env_backup_resource())


@atomic_installer
def env_backup_resource():
    veil_server_names = sorted(list_veil_servers(VEIL_ENV).keys())
    veil_server_names.remove('@guard')
    for veil_server_name in veil_server_names:
        bring_down_server(VEIL_ENV, veil_server_name)
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for veil_server_name in veil_server_names:
            backup_server(VEIL_ENV, veil_server_name, timestamp)
    finally:
        for veil_server_name in veil_server_names:
            bring_up_server(VEIL_ENV, veil_server_name)


def bring_down_server(backing_up_env, veil_server_name):
    deployed_via = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} down'.format(backing_up_env, veil_server_name))


def bring_up_server(backing_up_env, veil_server_name):
    deployed_via = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} up --daemonize'.format(backing_up_env, veil_server_name))


def backup_server(backing_up_env, veil_server_name, timestamp):
    fabric.api.env.host_string = get_veil_server_deploys_via(backing_up_env, veil_server_name)
    backup_path = '/backup/{}/{}-{}-{}.tar.gz'.format(
        timestamp, backing_up_env, veil_server_name, timestamp)
    with fabric.api.cd('/opt/{}/app'.format(backing_up_env)):
        fabric.api.sudo('veil :{}/{} backup {}'.format(
            backing_up_env, veil_server_name,
            backup_path))
    if not os.path.exists('/backup'):
        os.mkdir('/backup', 0755)
    if not os.path.exists('/backup/{}'.format(timestamp)):
        os.mkdir('/backup/{}'.format(timestamp), 0755)
    fabric.api.get(backup_path, backup_path)