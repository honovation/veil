from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *

@script('install')
def install_demo():
    execute_script('frontend', 'template', 'install')
    execute_script('supervisor', 'install')
    execute_script('frontend', 'web', 'nginx', 'install')
    execute_script('backend', 'database', 'postgresql', 'client', 'install')
    execute_script('backend', 'database', 'postgresql', 'server', 'install')
    execute_script('backend', 'redis', 'client', 'install')
    execute_script('backend', 'redis', 'server', 'install')
    execute_script('backend', 'queue', 'client', 'install')
    execute_script('backend', 'queue', 'server', 'install')
