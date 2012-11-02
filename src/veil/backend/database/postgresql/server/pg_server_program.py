from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

import os
import contextlib
import time
from veil.frontend.cli import *
from veil.backend.shell import *
from veil.environment.setting import *
from veil.utility.path import *
from veil.environment.installation import *
from veil.frontend.template import *

def postgresql_server_program(purpose, updates=None):
    program = {
        'execute_command': 'veil backend database postgresql server-up {}'.format(purpose),
        'install_command': 'veil backend database postgresql install-server {}'.format(purpose)
    }
    if updates:
        program.update(updates)
    return program


@script('server-up')
def bring_up_postgresql_server(purpose):
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(purpose))
    pass_control_to('postgres -D {}'.format(config.data_directory))


@installation_script('install-server')
def install_postgresql_server(purpose=None):
    if not purpose:
        return
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(purpose))
    install_ubuntu_package('postgresql-9.1')
    remove_service_auto_start('postgresql', '/etc/rc0.d/K21postgresql')
    pg_bin_dir = as_path('/usr/lib/postgresql/9.1/bin')
    assert pg_bin_dir.exists()
    global_bin_dir = as_path('/usr/bin')
    create_symbolic_link(global_bin_dir / 'psql', to='{}/psql'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'pg_dump', to='{}/pg_dump'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'initdb', to='{}/initdb'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'pg_ctl', to='{}/pg_ctl'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'postgres', to='{}/postgres'.format(pg_bin_dir))
    pg_data_dir = as_path(config.data_directory)
    no_user = False
    if not pg_data_dir.exists():
        old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.dirname()), capture=True).strip()
        shell_execute('chmod 777 {}'.format(pg_data_dir.dirname()))
        create_file('/tmp/pg-owner-password', config.owner_password)
        try:
            shell_execute(
                'su {pg_data_owner} -c "initdb  -E {encoding} --locale=en_US.UTF-8 -A md5 -U {pg_data_owner} --pwfile=/tmp/pg-owner-password {pg_data_dir}"'.format(
                    encoding='UTF8', pg_data_owner=config.owner, pg_data_dir=pg_data_dir
                ))
        finally:
            delete_file('/tmp/pg-owner-password')
        shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.dirname()))
        delete_file(pg_data_dir / 'postgresql.conf')
        delete_file(pg_data_dir / 'pg_hba.conf')
        delete_file(pg_data_dir / 'pg_ident.conf')
        no_user = True
    pg_config_dir = as_path(config.config_directory)
    create_directory(pg_config_dir)
    create_file(
        pg_config_dir / 'postgresql.conf',
        content=get_template('postgresql.conf.j2').render(config=config))
    create_file(pg_config_dir / 'pg_hba.conf', content=get_template('pg_hba.conf.j2').render(config=config))
    create_file(pg_config_dir / 'pg_ident.conf', content=get_template('pg_ident.conf.j2').render())
    create_symbolic_link(pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf')
    create_symbolic_link(pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf')
    create_symbolic_link(pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf')
    if no_user:
        pg_user = config.user
        assert pg_user, 'must specify postgresql user'
        pg_password = config.password
        assert pg_password, 'must specify postgresql user password'
        with postgresql_server_running(config):
            env = os.environ.copy()
            env['PGPASSWORD'] = config.owner_password
            shell_execute('psql -h {} -p {} -U {} -d postgres -c "{}"'.format(
                config.host, config.port, config.owner,
                "CREATE USER {} WITH PASSWORD '{}'".format(pg_user, pg_password)
            ), env=env)


@contextlib.contextmanager
def postgresql_server_running(config):
    shell_execute('su {} -c "pg_ctl -D {} start"'.format(
        config.owner, config.data_directory))
    time.sleep(5)
    try:
        yield
    finally:
        shell_execute('su {} -c "pg_ctl -D {} stop"'.format(
            config.owner, config.data_directory))