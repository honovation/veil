#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division
import sys
import os
import hashlib

# will be linked to $VEIL_HOME/.git/hooks/pre-commit by $VEIL_FRAMEWORK_HOME/bin/veil-init

def check():
    check_if_locked_migration_scripts_being_changed()


def check_if_locked_migration_scripts_being_changed():
    for purpose in os.listdir('./db'):
        file_names = set(os.listdir('./db/{}'.format(purpose)))
        for sql_file_name in file_names:
            locked_file_name = sql_file_name.replace('.sql', '.locked')
            if sql_file_name.endswith('.sql') and locked_file_name in file_names:
                expected_md5 = open('./db/{}/{}'.format(purpose, locked_file_name)).read()
                sql_path = './db/{}/{}'.format(purpose, sql_file_name)
                with open(sql_path) as f:
                    actual_md5 = calculate_file_md5_hash(f)
                if actual_md5 != expected_md5:
                    print('[Orz] LISTEN!!! Read after me: "I should not modify {}"'.format(sql_path))
                    sys.exit(1)


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


if __name__ == '__main__':
    check()