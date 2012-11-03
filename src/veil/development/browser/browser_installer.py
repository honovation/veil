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
    # spynner depends on lxml
    install_ubuntu_package('libxml2-dev')
    install_ubuntu_package('libxslt1-dev')
    install_python_package('spynner')
    install_python_package('selenium')
    if not os.path.exists('/usr/bin/chromedriver'):
        shell_execute('wget http://chromedriver.googlecode.com/files/chromedriver_linux64_21.0.1180.4.zip -O /tmp/chromedriver_linux64_21.0.1180.4.zip')
        shell_execute('unzip /tmp/chromedriver_linux64_21.0.1180.4.zip -d /usr/bin')