from __future__ import unicode_literals, print_function, division
import fabric.api
import datetime
import os
import logging
import time
from croniter.croniter import croniter
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.clock import get_current_timestamp

LOGGER = logging.getLogger(__name__)

@script('backup-env-at')
def backup_env_at(backing_up_env, crontab_expression):
    with open('{}/.backup-{}.pass'.format(os.getenv('HOME'), backing_up_env)) as f:
        user, password = f.read().split(':')
    fabric.api.user = user
    fabric.api.password = password
    while True:
        now = get_current_timestamp()
        next = croniter(crontab_expression, now).get_next()
        delta = next - now
        LOGGER.info('backup later: wake up in %(delta)s seconds', {
            'delta': delta
        })
        time.sleep(delta)
        backup_env(backing_up_env)


@script('backup-env')
def backup_env(backing_up_env):
    for veil_server_name in sorted(get_veil_servers(backing_up_env).keys()):
        bring_down_server(backing_up_env, veil_server_name)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    for veil_server_name in sorted(get_veil_servers(backing_up_env).keys()):
        if '@guard' != veil_server_name:
            backup_server(backing_up_env, veil_server_name, timestamp)
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
        fabric.api.sudo('veil :{}/{} up --daemonize'.format(backing_up_env, veil_server_name))


def backup_server(backing_up_env, veil_server_name, timestamp):
    deployed_via = get_remote_veil_server(backing_up_env, veil_server_name).deployed_via
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