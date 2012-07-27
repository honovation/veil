from __future__ import unicode_literals, print_function, division
from veil.script import *
from sandal.path import *
from sandal.shell import *
from sandal.template import *
from ....ubuntu_package import install_ubuntu_package, remove_service_auto_start
from ....filesystem import delete_file
from ....filesystem import create_symbolic_link
from ....filesystem import create_file
from ....setting import get_environment_settings
from .launcher import postgresql_server_running

@script('install')
def install_postgresql_server():
    settings = get_environment_settings()
    install_ubuntu_package('postgresql-9.1')
    pg_bin_dir = path('/usr/lib/postgresql/9.1/bin')
    assert pg_bin_dir.exists()
    global_bin_dir = path('/usr/bin')
    create_symbolic_link(global_bin_dir / 'psql', to='{}/psql'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'pg_dump', to='{}/pg_dump'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'initdb', to='{}/initdb'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'pg_ctl', to='{}/pg_ctl'.format(pg_bin_dir))
    create_symbolic_link(global_bin_dir / 'postgres', to='{}/postgres'.format(pg_bin_dir))
    remove_service_auto_start('postgresql', '/etc/rc0.d/K21postgresql')
    pg_data_dir = settings.postgresql.data_directory
    assert pg_data_dir, 'must specify postgresql data directory'
    pg_data_dir = path(pg_data_dir)
    pg_data_owner = settings.postgresql.data_owner
    assert pg_data_owner, 'must specify postgresql data owner'
    no_user = False
    if not pg_data_dir.exists():
        old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.dirname()), capture=True).strip()
        shell_execute('chmod 777 {}'.format(pg_data_dir.dirname()))
        shell_execute('su {pg_data_owner} -c "initdb -A md5 -U {pg_data_owner} -W {pg_data_dir}"'.format(
            pg_data_owner=pg_data_owner, pg_data_dir=pg_data_dir
        ))
        shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.dirname()))
        delete_file(pg_data_dir / 'postgresql.conf')
        delete_file(pg_data_dir / 'pg_hba.conf')
        delete_file(pg_data_dir / 'pg_ident.conf')
        no_user = True
    pg_config_dir = settings.postgresql.config_directory
    assert pg_config_dir, 'must specify postgresql config directory'
    pg_config_dir = path(pg_config_dir)
    create_file(
        pg_config_dir / 'postgresql.conf',
        content=get_template('postgresql.conf.j2').render(config=settings.postgresql))
    create_file(pg_config_dir / 'pg_hba.conf', content=get_template('pg_hba.conf.j2').render())
    create_file(pg_config_dir / 'pg_ident.conf', content=get_template('pg_ident.conf.j2').render())
    create_symbolic_link(pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf')
    create_symbolic_link(pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf')
    create_symbolic_link(pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf')
    if no_user:
        pg_user = settings.postgresql.user
        assert pg_user, 'must specify postgresql user'
        pg_password = settings.postgresql.password
        assert pg_password, 'must specify postgresql user password'
        with postgresql_server_running():
            shell_execute('psql -h {} -p {} -U {} -W -d postgres -c "{}"'.format(
                settings.postgresql.host,
                settings.postgresql.port,
                pg_data_owner,
                "CREATE USER {} WITH PASSWORD '{}' CREATEDB SUPERUSER".format(pg_user, pg_password)
            ))