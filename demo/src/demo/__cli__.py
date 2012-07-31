from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *

@script('install')
def install_demo():
    execute_script('environment', 'runtime', 'config-file', 'generate')
    execute_script('environment', 'runtime', 'supervisor', 'install')
    execute_script('frontend', 'web', 'nginx', 'install')
    execute_script('frontend', 'queue', 'install')
    execute_script('backend', 'rdbms', 'postgresql', 'client', 'install')
    execute_script('backend', 'rdbms', 'postgresql', 'server', 'install')
    execute_script('backend', 'redis', 'client', 'install')
    execute_script('backend', 'redis', 'server', 'install')
