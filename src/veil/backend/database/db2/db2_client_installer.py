from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

import os
from veil.backend.shell import *
from veil.environment.installation import *

@installation_script()
def install_db2_client():
    install_ubuntu_package('libaio1')
    install_ubuntu_package('libstdc++6-4.4-dev')
    install_ubuntu_package('libstdc++6-4.4-pic')
    install_ubuntu_package('libstdc++5')
    install_db2_driver()
    try:
        import ibm_db
    except:
        env = os.environ.copy()
        env['IBM_DB_HOME'] = '/opt/db2-clidriver'
        install_python_package('ibm_db', env=env)
        create_file('/etc/ld.so.conf.d/db2-clidriver.conf', '/opt/db2-clidriver/lib')
        shell_execute('ldconfig')


def install_db2_driver():
    if os.path.exists('/opt/db2-clidriver'):
        return
    shell_execute(
#        'wget http://dependency-veil.googlecode.com/svn/trunk/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz')
        'wget http://200.200.200.25:8080/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz')
    shell_execute('tar xzf /tmp/db2-clidriver.tar.gz -C /opt')