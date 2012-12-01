from __future__ import unicode_literals, print_function, division
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from veil.server.supervisor import *

@script('backup')
def backup(backup_path):
    if is_supervisord_running():
        raise Exception('can not backup while supervisord is executing')
    backup_dir = os.path.dirname(backup_path)
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, mode=0755)
    shell_execute('tar czf {} --exclude *.pid -C {} .'.format(
        backup_path, VEIL_VAR_DIR))