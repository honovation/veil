from __future__ import unicode_literals, print_function, division
import logging
from veil.utility.shell import *
from veil.frontend.cli import *
from veil.environment import *

LOGGER = logging.getLogger(__name__)

@script('pull')
def pull():
    pull_dir(VEIL_HOME)
    pull_dir(VEIL_FRAMEWORK_HOME)

def pull_dir(dir):
    LOGGER.info('pull %(workspace)s ...', {'workspace': dir})
    having_changes = shell_execute('git diff-index HEAD', capture=True, cwd=dir)
    if having_changes:
        shell_execute('git stash', cwd=dir)
    try:
        shell_execute('git pull --rebase', cwd=dir)
    finally:
        if having_changes:
            shell_execute('git stash pop --index', capture=True, cwd=dir)