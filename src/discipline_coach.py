#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals, print_function, division
import sys
import os
import shlex
import subprocess
import re
from veil.utility.encoding import *
from veil.utility.misc import *

# will be linked to $VEIL_HOME/.git/hooks/pre-commit by $VEIL_FRAMEWORK_HOME/bin/veil-init

FORBIDDEN_COMMIT_BRANCH_PREFIX = 'env-'
RE_MODIFIED = re.compile('^(?:M|A|\?\?|AM)(\s+)(?P<name>.*)')
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
    base_version, changes = get_git_dir_version()
    hashes = [base_version]
    for f, version in changes.items():
        hashes.append('{} {}'.format(f, version))
    return to_str('\n'.join(sorted(hashes)))


def get_git_dir_version(git_dir='.'):
    base_version = shell_execute('git log -n 1 --pretty=format:%H', capture=True, cwd=git_dir)
    out = shell_execute('git status --porcelain', capture=True, cwd=git_dir)
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
    for file in modified_files:
        if os.path.isfile(file):
            with open(os.path.join(git_dir, file)) as f:
                changes[file] = calculate_file_md5_hash(f)
    for file in deleted_files:
        changes[file] = 'DELETED'
    return base_version, changes


def shell_execute(command_line, capture=False, waits=True, **kwargs):
    command_args = shlex.split(command_line)
    if capture:
        kwargs.update(dict(stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE))
    process = subprocess.Popen(command_args, **kwargs)
    if not waits:
        return process
    output = process.communicate()[0]
    if process.returncode:
        if capture:
            raise Exception(
                'Subprocess return code: {}, command: {}, kwargs: {}, output: {}'.format(
                    process.returncode, command_args, kwargs, output))
        else:
            raise Exception(
                'Subprocess return code: {}, command: {}, kwargs: {}'.format(
                    process.returncode, command_args, kwargs))
    return output


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

red = _wrap_with('31')

if __name__ == '__main__':
    check_if_commit_in_forbidden_branch()
    check_if_self_check_passed()
