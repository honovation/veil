from __future__ import unicode_literals, print_function, division
from sandal.path import *
from veil.environment.installation import *
from veil.backend.shell import *
from veil.frontend.template import *
from veil.environment.setting import *
from .launcher import postgresql_server_running

@installation_script()
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
        shell_execute('su {pg_data_owner} -c "initdb -A md5 -U {pg_data_owner} -W {pg_data_dir}"'.format(
            pg_data_owner=config.owner, pg_data_dir=pg_data_dir
        ))
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
    create_file(pg_config_dir / 'pg_hba.conf', content=get_template('pg_hba.conf.j2').render())
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
            shell_execute('psql -h {} -p {} -U {} -W -d postgres -c "{}"'.format(
                config.host,
                config.port,
                config.owner,
                "CREATE USER {} WITH PASSWORD '{}' CREATEDB SUPERUSER".format(pg_user, pg_password)
            ))