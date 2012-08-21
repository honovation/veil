from __future__ import unicode_literals, print_function, division
import os.path
from veil.environment.installation import *
from veil.backend.shell import *

@installation_script()
def install_spynner():
    install_ubuntu_package('python-qt4')
    try:
        import PyQt4
    except ImportError:
        shell_execute(os.path.join(os.path.dirname(__file__), 'link-pyqt4-to-virtualenv.sh'))
    install_python_package('spynner')
    install_python_package('selenium')
