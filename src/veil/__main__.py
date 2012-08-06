from __future__ import unicode_literals, print_function, division
import sys
from veil.environment.runtime import *
from veil.frontend.cli import execute_script

__import__('veil.frontend.template')
__import__('veil.frontend.web.nginx')
__import__('veil.backend.queue')
__import__('veil.backend.database')
__import__('veil.backend.redis')
__import__('veil.environment.runtime')
__import__('veil.environment.deployment')
__import__('veil.environment.development')
__import__('__veil__')
execute_script(
    on_script_executing=lambda script_handler: bootstrap_runtime(script_handler.options),
    *sys.argv[1:])