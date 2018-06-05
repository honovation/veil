from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *
from veil.backend.database.client import *
from ...postgresql_setting import get_pg_bin_dir
from ..server.pg_server_installer import postgresql_maintenance_config

LOGGER = logging.getLogger(__name__)


@script('routines-up')
def bring_up_routines(purpose):
    @run_every('47 3 * * 2')
    def work():
        vacuum_and_reindex_db(purpose)

    work()


def vacuum_and_reindex_db(purpose):
    config = database_client_config(purpose)
    maintenance_config = postgresql_maintenance_config(purpose)
    pg_bin_dir = get_pg_bin_dir(maintenance_config.version)
    env = os.environ.copy()
    env['PGPASSWORD'] = maintenance_config.owner_password
    shell_execute('{pg_bin_dir}/vacuumdb -h {host} -p {port} -U {user} --all --full --analyze'.format(
        pg_bin_dir=pg_bin_dir,
        host=config.host,
        port=config.port,
        user=maintenance_config.owner), env=env)
    shell_execute('{pg_bin_dir}/reindexdb -h {host} -p {port} -U {user} --all'.format(
        pg_bin_dir=pg_bin_dir,
        host=config.host,
        port=config.port,
        user=maintenance_config.owner), env=env)
