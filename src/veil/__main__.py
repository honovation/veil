from __future__ import unicode_literals, print_function, division
import sys
from veil.environment.runtime import *
from veil.frontend.script import execute_script

bootstrap_runtime()
__import__('veil.frontend.web')
__import__('veil.frontend.queue')
__import__('veil.backend.rdbms')
__import__('veil.backend.redis')
__import__('veil.environment.runtime')
__import__('veil.environment.deployment')
__import__('veil.environment.development')
execute_script(*sys.argv[1:])