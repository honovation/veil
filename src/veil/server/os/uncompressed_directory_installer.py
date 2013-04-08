from __future__ import unicode_literals, print_function, division
import os
from veil_installer import *
from veil.utility.shell import *

@atomic_installer
def uncompressed_directory_resource(compressed_file, path):
    is_installed = os.path.exists(path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['uncompressed_directory?{}'.format(path)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    if compressed_file.endswith('.zip') or compressed_file.endswith('.jar'):
        shell_execute('unzip {} -d {}'.format(compressed_file, path), capture=True)
    elif compressed_file.endswith('.tar.gz'):
        os.makedirs(path, mode=0755)
        shell_execute('tar xzf {} -C {} --strip-components=1'.format(compressed_file, path), capture=True)
    else:
        raise Exception('do not know how to uncompress: {}'.format(compressed_file))