from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.environment.installation import *

__import__('demo.website')

@installation_script()
def install_demo():
    shell_execute('veil backend database postgresql server install demo')
    shell_execute('veil backend redis server install demo')
