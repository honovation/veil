from __future__ import unicode_literals, print_function, division
import os.path
from veil.environment.installation import *
from veil.backend.shell import *

@installation_script()
def install_pyqt4():
    install_ubuntu_package('python-qt4')
    shell_execute(os.path.join(os.path.dirname(__file__), 'link-qt4-to-virtualenv.sh'))
