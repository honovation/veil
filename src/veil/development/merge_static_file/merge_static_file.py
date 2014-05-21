# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
from cStringIO import StringIO
from veil.frontend.cli import *
from veil.utility.misc import *
from veil_component import *

STATIC_FILE_DIR = VEIL_HOME / 'static'
SUPPORT_STATIC_FILE_TYPES = ('js', 'css')


def list_static_file_dependencies():
    file_path = VEIL_HOME / 'DEP-STATIC-FILE'
    if not file_path.exists():
        return {}
    code = compile(file_path.text(), file_path, 'exec')
    context = {}
    exec(code, context)
    return context['STATIC_FILE_DEPENDENCIES']


@script('merge')
def merge():
    static_file_dep = list_static_file_dependencies()
    purposes = static_file_dep.keys()
    for purpose in purposes:
        file_types = static_file_dep[purpose].keys()
        for file_type in file_types:
            merge_files(purpose, file_type)


def merge_files(purpose, static_file_type):
    config = list_static_file_dependencies()[purpose]
    configs = config[static_file_type]
    if not configs:
        return
    for config in configs:
        output_file_name = config['output']
        files_to_merge = config['files']
        if not files_to_merge:
            continue
        with contextlib.closing(StringIO()) as buffer_:
            for file_path in files_to_merge:
                with open(STATIC_FILE_DIR / file_path, mode='rb') as f:
                    buffer_.write(f.read())
            buffer_.reset()
            new_md5 = calculate_file_md5_hash(buffer_, reset_position=True)
            current_md5 = None
            if (STATIC_FILE_DIR / output_file_name).exists():
                with open(STATIC_FILE_DIR / output_file_name) as f:
                    current_md5 = calculate_file_md5_hash(f)
            if current_md5 != new_md5:
                with open(STATIC_FILE_DIR / output_file_name, mode='wb') as f:
                    f.write(buffer_.read())
