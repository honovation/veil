from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import VEIL_HOME, VEIL_FRAMEWORK_HOME
from veil.utility.shell import *
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)


@script('pull')
def pull():
    pull_dir(VEIL_HOME)
    pull_dir(VEIL_FRAMEWORK_HOME)


def pull_dir(cwd):
    LOGGER.info('pull %(workspace)s ...', {'workspace': cwd})
    having_changes = has_changes_not_committed(cwd)
    if having_changes:
        shell_execute('git stash', cwd=cwd)
    try:
        shell_execute('git pull --rebase', cwd=cwd)
    finally:
        if having_changes:
            shell_execute('git stash pop --index', capture=True, cwd=cwd)


def has_changes_not_committed(cwd):
    return bool(shell_execute('git diff HEAD', capture=True, cwd=cwd))


def check_no_changes_not_committed():
    dirs = []
    if has_changes_not_committed(VEIL_HOME):
        dirs.append(VEIL_HOME)
    if has_changes_not_committed(VEIL_FRAMEWORK_HOME):
        dirs.append(VEIL_FRAMEWORK_HOME)
    if dirs:
        raise Exception('Local changes detected in {} !!!'.format(', '.join(dirs)))


def has_commits_not_pushed(cwd):
    return bool(shell_execute('git log origin/$(git rev-parse --abbrev-ref HEAD)..HEAD', capture=True, cwd=cwd, debug=True))


def check_no_commits_not_pushed():
    dirs = []
    if has_commits_not_pushed(VEIL_HOME):
        dirs.append(VEIL_HOME)
    if has_commits_not_pushed(VEIL_FRAMEWORK_HOME):
        dirs.append(VEIL_FRAMEWORK_HOME)
    if dirs:
        raise Exception('Local commits not pushed detected in {} !!!'.format(', '.join(dirs)))
