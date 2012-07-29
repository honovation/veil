from __future__ import unicode_literals, print_function, division
import sys
from veil.environment.runtime import *
from veil.script import execute_script

bootstrap_runtime()
__import__('veil._script')
__import__('veil.web')
__import__('veil.database')
__import__('veil.supervisor')
__import__('veil.pycharm')
execute_script(sys.argv[1:])