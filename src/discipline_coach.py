#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division
import sys
import os
import hashlib
import shlex
import subprocess
import re

# will be linked to $VEIL_HOME/.git/hooks/pre-commit by $VEIL_FRAMEWORK_HOME/bin/veil-init

def check_if_self_check_passed():
    if not is_self_check_passed():
        print('[Orz] LISTEN!!! Read after me: "I should run veil self-check before commit"')
        sys.exit(1)


def is_self_check_passed():
    if not os.path.exists('./.self-check-passed'):
        return False
    with open('./.self-check-passed') as f:
        expected_hash = f.read()
    actual_hash = calculate_git_status_hash()
    return expected_hash == actual_hash


def calculate_git_status_hash():
    RE_MODIFIED = re.compile('^(?:M|A)(\s+)(?P<name>.*)')
    hashes = [shell_execute('git log -n 1 --pretty=format:%H', capture=True)]
    files = []
    out = shell_execute('git status --porcelain', capture=True)
    for line in out.splitlines():
        match = RE_MODIFIED.match(line.strip())
        if match:
            files.append(match.group('name'))
    for file in files:
        with open(file) as f:
            hashes.append(calculate_file_md5_hash(f))
    return  '\n'.join(sorted(hashes))


def calculate_file_md5_hash(file_object, reset_position=False, hex=True):
    """ Calculate the md5 hash for this file.

    This reads through the entire file.
    """
    assert file_object is not None and file_object.tell() == 0
    try:
        m = hashlib.md5()
        for chunk in iter_file_in_chunks(file_object):
            m.update(chunk)
        return m.hexdigest() if hex else m.digest()
    finally:
        if reset_position:
            file_object.seek(0)


def iter_file_in_chunks(file_object, chunk_size=8192):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k."""
    return iter(lambda: file_object.read(chunk_size), b'')


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


if __name__ == '__main__':
    check_if_self_check_passed()