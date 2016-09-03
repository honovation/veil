#! env/bin/python
# -*- coding: UTF-8 -*-
"""
will be linked to $VEIL_HOME/.git/hooks/pre-commit by $VEIL_FRAMEWORK_HOME/bin/veil-init
"""

from __future__ import unicode_literals, print_function, division
import sys
import os
import re
import logging
from veil_component import red
from veil.utility.encoding import *
from veil.utility.misc import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

FORBIDDEN_COMMIT_BRANCH_PREFIX = 'env-'
RE_MODIFIED = re.compile('^(?:M|A|\?\?|AM|MM|\sM)(\s+)(?P<name>.*)')
RE_DELETED = re.compile('^(?:D)(\s+)(?P<name>.*)')


def check_if_self_check_passed():
    if not is_self_check_passed():
        print(red('[Orz] LISTEN!!! Read after me: "I should run veil self-check before commit"'))
        sys.exit(1)


def check_if_commit_in_forbidden_branch():
    current_branch = shell_execute('git rev-parse --abbrev-ref HEAD', capture=True)
    if current_branch.startswith(FORBIDDEN_COMMIT_BRANCH_PREFIX):
        print(red('[Orz] LISTEN!!! Read after me: "I should not commit in this branch"'))
        sys.exit(-1)


def is_self_check_passed():
    if not os.path.exists('./.self-check-passed'):
        return False
    with open('./.self-check-passed') as f:
        expected_hash = f.read()
    actual_hash = calculate_git_status_hash()
    return expected_hash == actual_hash


def calculate_git_status_hash():
    while 1:
        try:
            base_version, changes = get_git_dir_version()
        except ShellExecutionError:
            pass
        else:
            hashes = [base_version]
            for f, version in changes.items():
                hashes.append('{} {}'.format(f, version))
            return to_str('\n'.join(sorted(hashes)))


def get_git_dir_version(git_dir='.'):
    base_version = shell_execute('git log -n 1 --pretty=format:%H', capture=True, cwd=git_dir)
    out = shell_execute('cp {index_path} {other_index_path} && GIT_INDEX_FILE={other_index_path} git status --porcelain'.format(
        index_path='{}/.git/index'.format(git_dir), other_index_path='{}/.git/other-index'.format(git_dir)), capture=True, cwd=git_dir)
    modified_files = []
    deleted_files = []
    for line in out.splitlines():
        match = RE_MODIFIED.match(line.strip())
        if match:
            modified_files.append(to_unicode(match.group('name')))
        match = RE_DELETED.match(line.strip())
        if match:
            deleted_files.append(to_unicode(match.group('name')))
    changes = {}
    for path in modified_files:
        if os.path.isfile(os.path.join(git_dir, path)):
            with open(os.path.join(git_dir, path)) as f:
                changes[path] = calculate_file_md5_hash(f)
    for path in deleted_files:
        changes[path] = 'DELETED'
    return base_version, changes


if __name__ == '__main__':
    check_if_commit_in_forbidden_branch()
    check_if_self_check_passed()
