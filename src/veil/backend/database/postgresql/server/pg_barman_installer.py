# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import CURRENT_USER, CURRENT_USER_GROUP, VEIL_ETC_DIR, VEIL_LOG_DIR, VEIL_BARMAN_DIR
from veil.server.config import *
from veil.server.os import *
from veil_installer import *
from ...postgresql_setting import get_pg_bin_dir

BARMAN_CONF_PATH = VEIL_ETC_DIR / 'barman.d'


@composite_installer
def pgbarman_resource(config):
    barman_server_config = render_config('pg_barman_server.conf.j2', server_name=config.server_name, db_host=config.db_host, db_user=config.db_user,
                                         replication_user=config.replication_user, pg_bin_path=get_pg_bin_dir(config.pg_version),
                                         barman_server_home=VEIL_BARMAN_DIR / config.server_name)
    resources = [
        postgresql_apt_repository_resource(),
        os_package_resource(name='barman'),
        directory_resource(path=BARMAN_CONF_PATH, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=VEIL_BARMAN_DIR / config.server_name, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path='/tmp/barman.conf', content=render_config('pg_barman.conf.j2', barman_user=CURRENT_USER, server_conf_path=BARMAN_CONF_PATH,
                                                                     barman_home=VEIL_BARMAN_DIR, log_path=VEIL_LOG_DIR), owner=CURRENT_USER,
                      group=CURRENT_USER_GROUP, cmd_run_after_updated='sudo mv /tmp/barman.conf /etc/barman.conf'),
        file_resource(path=BARMAN_CONF_PATH / '{}.conf'.format(config.server_name), content=barman_server_config, owner=CURRENT_USER, group=CURRENT_USER_GROUP,
                      cmd_run_after_updated='barman receive-wal --create-slot {}'.format(config.server_name)),
        file_resource(path='/tmp/barman', content=render_config('pg_barman_cron.d.j2', barman_user=CURRENT_USER), owner=CURRENT_USER, group=CURRENT_USER_GROUP,
                      cmd_run_after_updated='sudo mv /tmp/barman /etc/cron.d/barman && sudo chown root:root /etc/cron.d/barman && sudo chmod 444 /etc/cron.d/barman')
    ]

    return resources
