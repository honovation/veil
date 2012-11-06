from __future__ import unicode_literals, print_function, division
import os
from veil_installer import *
from veil.backend.shell import *

@installer('python_qt4')
def install_python_qt4(dry_run_result):
    is_installed = is_os_package_installed('python-qt4')
    if dry_run_result is not None:
        dry_run_result['python_qt4'] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    install_os_package(None, 'python-qt4')
    shell_execute(os.path.join(os.path.dirname(__file__), 'link-pyqt4-to-virtualenv.sh'))