from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.backend.shell import *
from veil.environment.setting import *
from veil.utility.hash import *
import os


DB_DUMP_DIR = '/tmp/db_dump'

@script('deploy')
def deploy():
    shell_execute('veil install-supervisor')
#    generate_db_dump('before')
    shell_execute('veil down')
    shell_execute('veil install-component ljmall')
    shell_execute('veil ljmall backup deploy_backup')
    shell_execute('veil install')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate', capture=True)

@script('deploy-restore-check')
def deploy_restore_check():
    generate_db_dump('after')
    settings = get_settings()
    for key in settings.keys():
        if key.endswith('_postgresql'):
            purpose = key.replace('_postgresql','')
            if not os.path.exists('{}/{}.before'.format(DB_DUMP_DIR, purpose)):
                print('no before version!!!')
                return False
            else:
                before_md5 = get_md5_by_path('{}/{}.before'.format(DB_DUMP_DIR, purpose))
                after_md5 = get_md5_by_path('{}/{}.after'.format(DB_DUMP_DIR, purpose))
                if before_md5 != after_md5:
                    print('before version and after version is not valid!!!')
                    return False
    return True


def generate_db_dump(dump_type):
    if not os.path.exists(DB_DUMP_DIR):
        os.mkdir(DB_DUMP_DIR)
    settings = get_settings()
    for key in settings.keys():
        if key.endswith('_postgresql'):
            config = getattr(settings, '{}'.format(key))
            shell_execute('export PGPASSWORD={};pg_dump -a -h {} -p {} -U {} {} > {}/{}.{}'.format(
                config.owner_password, config.host, config.port,
                config.owner, key.replace('_postgresql',''), DB_DUMP_DIR,
                key, dump_type))

def get_md5_by_path(path):
    with open(path) as f:
        md5 = calculate_file_md5_hash(f)
        return md5
