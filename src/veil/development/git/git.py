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


def pull_dir(cwd):
    LOGGER.info('pull %(workspace)s ...', {'workspace': cwd})
    having_changes = has_local_changes(cwd)
    if having_changes:
        shell_execute('git stash', cwd=cwd)
    try:
        shell_execute('git pull --rebase', cwd=cwd)
    finally:
        if having_changes:
            shell_execute('git stash pop --index', capture=True, cwd=cwd)


def has_local_changes(cwd):
    return bool(shell_execute('git diff-index HEAD', capture=True, cwd=cwd))


def check_no_local_changes():
    dirs = []
    if has_local_changes(VEIL_HOME):
        dirs.append(VEIL_HOME)
    if has_local_changes(VEIL_FRAMEWORK_HOME):
        dirs.append(VEIL_FRAMEWORK_HOME)
    if dirs:
        print('Local changes detected in {} !!!'.format(', '.join(dirs)))
        exit(-1)


def has_local_commits_not_pushed(cwd):
    return bool(shell_execute('git log origin/master..HEAD', capture=True, cwd=cwd))


def check_all_local_commits_pushed():
    dirs = []
    if has_local_commits_not_pushed(VEIL_HOME):
        dirs.append(VEIL_HOME)
    if has_local_commits_not_pushed(VEIL_FRAMEWORK_HOME):
        dirs.append(VEIL_FRAMEWORK_HOME)
    if dirs:
        print('Local commits not pushed detected in {} !!!'.format(', '.join(dirs)))
        exit(-1)
