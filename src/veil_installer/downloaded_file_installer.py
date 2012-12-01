from __future__ import unicode_literals, print_function, division
import os.path
from .installer import atomic_installer
from .installer import get_dry_run_result
from .shell import shell_execute

@atomic_installer
def downloaded_file_resource(url, path):
    is_installed = os.path.exists(path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['downloaded_file?{}'.format(path)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    shell_execute('wget {} -O {}'.format(url, path))