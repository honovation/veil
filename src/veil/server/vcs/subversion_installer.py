from __future__ import unicode_literals, print_function, division
import os
from veil_installer import *
from veil.server.os import *
from veil.utility.shell import *

@composite_installer
def subversion_repository_resource(url, path):
    resources = [
        os_package_resource(name='subversion'),
        subversion_repository_checked_out_resource(url=url, path=path),
        subversion_repository_updated_resource(path=path)]
    return resources


@atomic_installer
def subversion_repository_checked_out_resource(url, path):
    installed = os.path.exists('{}/.svn'.format(path))
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['subversion_repository_checked_out?{}'.format(path)] = '-' if installed else 'CHECKOUT'
        return
    if installed:
        return
    shell_execute('svn co {} {}'.format(url, path))


@atomic_installer
def subversion_repository_updated_resource(path):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['subversion_repository_updated?{}'.format(path)] = 'UPDATE'
        return
    shell_execute('svn up {}'.format(path))