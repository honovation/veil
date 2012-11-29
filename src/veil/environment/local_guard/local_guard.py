from __future__ import unicode_literals, print_function, division
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from veil.environment.supervisor import *

@script('backup')
def backup(backup_path):
    if is_supervisord_running():
        raise Exception('can not backup while supervisord is executing')
    os.makedirs(os.path.dirname(backup_path), mode=0755)
    shell_execute('tar czf {} --exclude *.pid -C {} .'.format(
        backup_path, VEIL_VAR_DIR))