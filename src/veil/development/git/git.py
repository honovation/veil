from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.frontend.cli import *
from veil.environment import *

@script('pull')
def pull():
    pull_dir(VEIL_HOME)
    pull_dir(VEIL_FRAMEWORK_HOME)

def pull_dir(dir):
    print('pull {} ...'.format(dir))
    having_changes = shell_execute('git diff-index HEAD', capture=True, cwd=dir)
    if having_changes:
        shell_execute('git stash', cwd=dir)
    try:
        shell_execute('git pull --rebase', cwd=dir)
    finally:
        if having_changes:
            shell_execute('git stash pop', capture=True, cwd=dir)