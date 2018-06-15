from __future__ import unicode_literals, print_function, division
import fabric.api
from datetime import datetime
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *
from .sync_to_backup_mirror import sync_to_backup_mirror

LOGGER = logging.getLogger(__name__)

KEEP_BACKUP_FOR_DAYS = 5 if VEIL_ENV.is_staging else 10


@script('host-backup')
def backup_host_script(crontab_expression):
    @run_every(crontab_expression)
    def work():
        create_host_backup()

    work()


@script('create-host-backup')
@log_elapsed_time
def create_host_backup():
    server_guard = get_current_veil_server()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_host(server_guard, timestamp)
    shell_execute('rm -f latest && ln -s {} latest'.format(timestamp), cwd=VEIL_BACKUP_ROOT)
    delete_old_backups()
    rsync_to_backup_mirror(server_guard)


@log_elapsed_time
def backup_host(server, timestamp):
    backup_dir = VEIL_BACKUP_ROOT / VEIL_ENV.name / server.host_base_name / timestamp
    if not VEIL_BACKUP_ROOT.exists():
        shell_execute('sudo mkdir -m 0700 {}'.format(VEIL_BACKUP_ROOT))
        shell_execute('sudo chown {}:{} {}'.format(server.ssh_user, server.ssh_user, VEIL_BACKUP_ROOT))
    if not backup_dir.exists():
        shell_execute('mkdir -p -m 0700 {}'.format(backup_dir))
    exclude_paths = [server.var_dir.relpathto(VEIL_BUCKET_INLINE_STATIC_FILES_DIR),
                     server.var_dir.relpathto(VEIL_BUCKET_CAPTCHA_IMAGE_DIR),
                     server.var_dir.relpathto(VEIL_BUCKET_UPLOADED_FILES_DIR),
                     server.var_dir.relpathto(VEIL_DATA_DIR) / '*-postgresql-*']
    excludes = ' '.join('--exclude "/{}"'.format(path) for path in exclude_paths)
    shell_execute(
        'rsync -avh --numeric-ids --delete {excludes} --link-dest={var_path}/ {var_path}/ {backup_dir}/'.format(excludes=excludes, var_path=server.var_dir,
                                                                                                                backup_dir=backup_dir))


def delete_old_backups():
    shell_execute('find . -maxdepth 1 -mindepth 1 -type d -ctime +{} -exec rm -r {{}} +'.format(KEEP_BACKUP_FOR_DAYS), cwd=VEIL_BACKUP_ROOT, debug=True)


def rsync_to_backup_mirror(server_guard):
    backup_mirror = server_guard.backup_mirror
    if not backup_mirror:
        return
    backup_mirror_path = '~/backup_mirror/{}/{}'.format(VEIL_ENV.name, server_guard.host_base_name)
    with fabric.api.settings(host_string=backup_mirror.deploys_via, user=backup_mirror.ssh_user, port=backup_mirror.ssh_port, key_filename=SSH_KEY_PATH):
        fabric.api.run('mkdir -p {}'.format(backup_mirror_path))
    sync_to_backup_mirror(backup_mirror, '{}/'.format(VEIL_BACKUP_ROOT), '/')
