from __future__ import unicode_literals, print_function, division
from datetime import datetime
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.timer import *
from veil.utility.shell import *
from .sync_to_backup_mirror import sync_to_backup_mirror

LOGGER = logging.getLogger(__name__)

KEEP_BACKUP_FOR_DAYS = 7 if VEIL_ENV.is_prod else 2


@script('host-backup')
def backup_host_script(crontab_expression):
    @run_every(crontab_expression)
    def work():
        create_host_backup()

    work()


@script('create-host-backup')
@log_elapsed_time
def create_host_backup():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_dir = backup_host(timestamp)
    shell_execute('rm -f latest && ln -s {} latest'.format(timestamp), cwd=backup_dir)
    delete_old_backups(backup_dir)
    sync_to_backup_mirror('{}/'.format(backup_dir), 'periodical-backup')


@log_elapsed_time
def backup_host(timestamp):
    server = get_current_veil_server()
    assert server.is_guard, 'only guard should backup host'
    if not VEIL_BACKUP_ROOT.exists():
        shell_execute('sudo mkdir -m 0700 {}'.format(VEIL_BACKUP_ROOT))
        shell_execute('sudo chown {}:{} {}'.format(server.ssh_user, server.ssh_user, VEIL_BACKUP_ROOT))
    backup_dir = VEIL_BACKUP_ROOT / VEIL_ENV.name / server.host_base_name
    if not backup_dir.exists():
        shell_execute('mkdir -p -m 0700 {}'.format(backup_dir))
    exclude_paths = [server.var_dir.relpathto(VEIL_BUCKET_INLINE_STATIC_FILES_DIR),
                     server.var_dir.relpathto(VEIL_BUCKET_CAPTCHA_IMAGE_DIR),
                     server.var_dir.relpathto(VEIL_BUCKET_UPLOADED_FILES_DIR),
                     server.var_dir.relpathto(VEIL_BARMAN_DIR),
                     server.var_dir.relpathto(VEIL_DATA_DIR) / '*-postgresql-*']
    excludes = ' '.join('--exclude "/{}"'.format(path) for path in exclude_paths)
    latest_dir = backup_dir / 'latest'
    link_dest = '--link-dest={}/'.format(latest_dir) if latest_dir.exists() else ''
    shell_execute('rsync -avh --numeric-ids --delete {} {} {}/ {}/{}/'.format(excludes, link_dest, server.var_dir, backup_dir, timestamp), expected_return_codes=(0, 24))
    if VEIL_BARMAN_DIR.exists():
        shell_execute('rsync -avh --numeric-ids --delete {} {}/'.format(VEIL_BARMAN_DIR, backup_dir), expected_return_codes=(0, 24))
    return backup_dir


def delete_old_backups(backup_dir):
    shell_execute('find . -maxdepth 1 -mindepth 1 -type d -ctime +{} -exec rm -r {{}} +'.format(KEEP_BACKUP_FOR_DAYS), cwd=backup_dir, debug=True)
