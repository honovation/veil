# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import CURRENT_USER, CURRENT_USER_GROUP, VEIL_ETC_DIR, VEIL_LOG_DIR, VEIL_VAR_DIR
from veil.server.config import *
from veil.server.os import *
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
