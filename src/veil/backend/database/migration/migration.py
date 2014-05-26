# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import os
from veil.environment import VEIL_HOME
from veil_component import as_path
from veil.utility.misc import *
from veil.frontend.cli import *


def load_versions(purpose):
    migration_script_dir = VEIL_HOME / 'db' / purpose
    versions = {}
    for migration_script in migration_script_dir.files('*.sql'):
        _, file_name = migration_script.splitpath()
        if '-' not in file_name:
            raise Exception('invalid migration script name: {}'.format(file_name))
        version = int(file_name.split('-')[0])
        if version in versions:
            raise Exception('{} duplicated with {}'.format(file_name, versions[version]))
        versions[version] = migration_script
    return versions


@script('lock-migration-scripts')
def lock_migration_scripts(purpose):
    migration_script_dir = VEIL_HOME / 'db' / purpose
    for sql_path in migration_script_dir.files('*.sql'):
        with open(sql_path) as sql_file:
            md5 = calculate_file_md5_hash(sql_file)
        lock_path = as_path(sql_path.replace('.sql', '.locked'))
        lock_path.write_text(md5)


def check_if_locked_migration_scripts_being_changed():
    if not os.path.exists(VEIL_HOME / 'db'):
        return
    for purpose in os.listdir(VEIL_HOME / 'db'):
        file_names = set(os.listdir(VEIL_HOME / 'db' / purpose))
        for sql_file_name in file_names:
            locked_file_name = sql_file_name.replace('.sql', '.locked')
            if sql_file_name.endswith('.sql') and locked_file_name in file_names:
                expected_md5 = open(VEIL_HOME / 'db' / purpose / locked_file_name).read()
                sql_path = VEIL_HOME / 'db' / purpose / sql_file_name
                with open(sql_path) as f:
                    actual_md5 = calculate_file_md5_hash(f)
                if actual_md5 != expected_md5:
                    raise Exception('locked migration script {} should not be changed'.format(sql_path))


def check_all_locked_migration_scripts():
    if not os.path.exists(VEIL_HOME / 'db'):
        return
    migration_script_dir = VEIL_HOME / 'db'
    purposes = migration_script_dir.dirs()
    for purpose in purposes:
        locked_file_count = len(purpose.files('*.locked'))
        script_file_count = len(purpose.files('*.sql'))
        if locked_file_count < script_file_count:
            print('You must lock scripts in {} using: veil backend database migration lock-migration-scripts {}'.format(purpose, purpose))
            exit(-1)
        else:
            print('Migration script check in {} ...passed!'.format(purpose))