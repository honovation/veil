from __future__ import unicode_literals, print_function, division
import fabric.api
import datetime
import os
from veil.frontend.cli import *
from veil.environment import *

@script('backup-env')
def backup_env():
    for veil_server_name in sorted(get_veil_servers(VEIL_ENV).keys()):
        bring_down_server(veil_server_name)
    for veil_server_name in sorted(get_veil_servers(VEIL_ENV).keys()):
        backup_server(veil_server_name)
    for veil_server_name in sorted(get_veil_servers(VEIL_ENV).keys()):
        bring_up_server(veil_server_name)


def bring_down_server(veil_server_name):
    deployed_via = get_remote_veil_server(VEIL_ENV, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(VEIL_ENV)):
        fabric.api.sudo('veil :{}/{} down'.format(VEIL_ENV, veil_server_name))


def bring_up_server(veil_server_name):
    deployed_via = get_remote_veil_server(VEIL_ENV, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    with fabric.api.cd('/opt/{}/app'.format(VEIL_ENV)):
        fabric.api.sudo('veil :{}/{} up'.format(VEIL_ENV, veil_server_name))


def backup_server(veil_server_name):
    deployed_via = get_remote_veil_server(VEIL_ENV, veil_server_name).deployed_via
    fabric.api.env.host_string = deployed_via
    backup_path = '/backup/{}-{}-{}.tar.gz'.format(
        VEIL_ENV, veil_server_name,
        datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    with fabric.api.cd('/opt/{}/app'.format(VEIL_ENV)):
        fabric.api.sudo('veil :{}/{} backup {}'.format(
            VEIL_ENV, veil_server_name,
            backup_path))
    os.mkdir('/backup', mode=0755)
    fabric.api.get(backup_path, backup_path)