# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import CURRENT_USER, CURRENT_USER_GROUP, VEIL_ETC_DIR, VEIL_LOG_DIR, VEIL_VAR_DIR
from veil.frontend.cli import *
from veil.model.collection import objectify
from veil.server.config import *
from veil.server.os import *
from veil.utility.shell import *
from veil.utility.timer import *
from veil_installer import *

BARMAN_CONF_PATH = VEIL_ETC_DIR / 'barman.d'
BARMAN_HOME = VEIL_VAR_DIR / 'barman'


@composite_installer
def pgbarman_resource(config):
    resources = [
        postgresql_apt_repository_resource(),
        os_package_resource(name='barman'),
        directory_resource(path=BARMAN_CONF_PATH, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=BARMAN_HOME, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=BARMAN_HOME / config.server_name, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path='/etc/cron.d/barman', content=render_config('pg_barman_cron.d.j2', barman_user=CURRENT_USER)),
        file_resource(path='/etc/barman.conf', content=render_config('pg_barman.conf.j2', barman_user=CURRENT_USER, server_conf_path=BARMAN_CONF_PATH,
                                                                     barman_home=BARMAN_HOME, log_path=VEIL_LOG_DIR)),
        file_resource(path=BARMAN_CONF_PATH / '{}.conf'.format(config.server_name), content=render_config('pg_barman_server.conf.j2',
                                                                                                          server_name=config.server_name,
                                                                                                          db_host=config.db_host,
                                                                                                          db_user=config.db_user,
                                                                                                          replication_user=config.replication_user,
                                                                                                          replication_slot_name=config.replication_slot_name,
                                                                                                          pg_bin_path=config.pg_bin_path,
                                                                                                          barman_server_home=BARMAN_HOME / config.server_name))
    ]
    return resources


@script('barman-backup')
def bring_up_barman_backup(crontab_expression, server_name):
    @run_every(crontab_expression)
    def work():
        try:
            shell_execute('barman backup {}'.format(server_name), capture=True)
        except:
            pass

    work()


def barman_periodic_backup_program(crontab_expression, server_name):
    return objectify({
        'barman_backup': {
            'execute_command': 'veil backend database postgresql barman-backup "{}" {}'.format(crontab_expression, server_name)
        }
    })


@script('barman-recover')
def bring_up_barman_recover(crontab_expression, server_name, host, port, user, path):
    @run_every(crontab_expression)
    def work():
        ssh_command = 'ssh -p {} {}@{}'.format(port, user, host)
        try:
            shell_execute('barman recover --remote-ssh-command "{}" {} latest {}'.format(ssh_command, server_name, path), capture=True)
        except:
            pass

    work()


def barman_periodic_recover_program(crontab_expression, server_name, host, port, user, path):
    return objectify({
        'barman_recover': {
            'execute_command': 'veil backend database postgresql barman-recover "{}" {} {} {} {} {}'.format(crontab_expression, server_name, host, port, user,
                                                                                                            path)
        }
    })
