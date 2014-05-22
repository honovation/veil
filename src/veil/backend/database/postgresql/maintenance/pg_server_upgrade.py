# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import sys
from veil.frontend.cli import *
from veil.profile.installer import *
from ...postgresql_setting import get_pg_config_dir, get_pg_data_dir, get_pg_bin_dir
from ..server.pg_server_installer import postgresql_server_resource

LOGGER = logging.getLogger(__name__)


@script('upgrade-server')
def upgrade_server(purpose, new_version):
    postgresql_program = get_current_veil_server().programs.get('{}_postgresql'.format(purpose))
    if not postgresql_program:
        LOGGER.error('cannot find out postgresql program, please run this on the veil server hosting postgresql server')
        exit(-1)
    config = None
    for resource in postgresql_program.resources:
        if resource[0] == 'veil.backend.database.postgresql.postgresql_server_resource':
            config = resource[1].config
            break
    old_version, config.version = config.version, new_version
    install_resource([
        postgresql_server_resource(purpose=purpose, config=config),
        os_package_resource(name='postgresql-server-dev-{}'.format(new_version))
    ])

    upgrade_postgresql_server(purpose, old_version, new_version, True)
    confirm_upgrading(purpose, old_version, new_version)
    upgrade_postgresql_server(purpose, old_version, new_version, False)

    installer_resource([
        symbolic_link_resource(path=get_pg_config_dir(purpose), to=get_pg_config_dir(purpose, new_version)),
    ])


def upgrade_postgresql_server(purpose, old_version, new_version, check_only):
    if check_only:
        LOGGER.warn('Checking postgresql server upgrading: %(old_version)s => %(new_version)s', {'old_version': old_version, 'new_version': new_version})
    else:
        LOGGER.warn('Upgrading postgresql server: %(old_version)s => %(new_version)s', {'old_version': old_version, 'new_version': new_version})
    shell_execute('''
        su - postgres '{new_bin_dir}/pg_upgrade {check_only} -j {cpu_cores} -b {old_bin_dir} -B {new_bin_dir} -d {old_data_dir} -D {new_data_dir} -o "-c config_file={old_data_dir}/postgresql.conf" -O "-c config_file={new_data_dir}/postgresql.conf"'
        '''.format(
        check_only='-c' if check_only else '', cpu_cores=shell_execute('nproc', capture=True),
        old_bin_dir=get_pg_bin_dir(old_version), old_data_dir=get_pg_data_dir(purpose, old_version),
        new_bin_dir=get_pg_bin_dir(new_version), new_data_dir=get_pg_data_dir(purpose, new_version)
    ), capture=True)


def confirm_upgrading(purpose, old_version, new_version):
    msg = 'upgrade from {} to {}'.format(old_version, new_version)
    print('type "{}" to continue:'.format(msg))
    while True:
        if msg == sys.stdin.readline().strip():
            break
