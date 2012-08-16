from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.setting import *

@script('install')
def install_redis_client():
    install_python_package('redis')