from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@script('deploy')
def deploy():
    shell_execute('veil install component?veil.environment.supervisor')
    shell_execute('veil down')
    rename_old_dirs()
    shell_execute('veil install component?ljmall')
    shell_execute('veil ljmall backup deploy_backup')
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')


@script('rename-old-dirs')
def rename_old_dirs():
    rename_old_dir(VEIL_VAR_DIR)
    rename_old_dir(VEIL_ETC_DIR)


def rename_old_dir(dir):
    existing_names = os.listdir(dir)
    for file in dir.listdir():
        if '_' in file.name:
            new_name = file.name.replace('_', '-')
            if new_name in existing_names:
                LOGGER.info('skip rename {} to {}, as same name exists'.format(file.name, new_name))
            else:
                LOGGER.info('rename {} to {}'.format(file.name, new_name))
                file.rename(dir / new_name)
