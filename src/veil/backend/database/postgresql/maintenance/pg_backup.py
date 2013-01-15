from __future__ import unicode_literals, print_function, division
import os
from veil.frontend.cli import *
from veil.backend.database.client import *
from veil.utility.shell import *

#pg_dump --host 10.24.3.10 --port 5432 --username "veil" --no-password  --format tar --blobs --verbose --file "/home/dejavu/dump" "ljmall"
#pg_restore --host localhost --port 5432 --username "veil" --no-password  --format tar --verbose -c -d ljmall /home/dejavu/dump.tar

@script('create-backup')
def create_backup(purpose, backup_path):
    config = load_database_client_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = config.password
    shell_execute('pg_dump --host {host} --port {port} --username {user} --format tar --blobs --verbose --file "{backup_path}" {database}'.format(
        host=config.host,
        port=config.port,
        user=config.user,
        backup_path=backup_path,
        database=config.database), env=env)

@script('restore-backup')
def restore_backup(backup_path, purpose):
    config = load_database_client_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = config.password
    shell_execute('pg_restore --host {host} --port {port} --username {user} --format tar --verbose -c -d {database} "{backup_path}"'.format(
        host=config.host,
        port=config.port,
        user=config.user,
        backup_path=backup_path,
        database=config.database), env=env)
