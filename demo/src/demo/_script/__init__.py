from __future__ import unicode_literals, print_function, division
from veil.frontend.web.server import *
from veil.frontend.script import *

@script('up')
def bring_up_demo():
    start_website(website='DEMO')


@script('install')
def install_demo():
    execute_script('environment', 'runtime', 'config-file', 'generate')
    execute_script('environment', 'runtime', 'supervisor', 'install')
    execute_script('frontend', 'web', 'nginx', 'install')
    execute_script('backend', 'rdbms', 'postgresql', 'client', 'install')
    execute_script('backend', 'rdbms', 'postgresql', 'server', 'install')
    execute_script('backend', 'redis', 'client', 'install')
    execute_script('backend', 'redis', 'server', 'install')
